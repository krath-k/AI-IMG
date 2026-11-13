"""
test_system.py
Comprehensive integration test suite for the AI Image Detector System.
Tests authentication, validation, FFT/spatial engine, heatmap generation,
circuit breaker fallback, PDF/JSON reporting, and Flask endpoints.
"""

import os
import sys
import io
import json
import unittest
import numpy as np
from PIL import Image as PILImage, ImageDraw, PngImagePlugin

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.database import User, Image as ImageModel, AIImageDetector, DetectionResult, Report, AuditLog
from services.auth_service import AuthService
from services.detection_engine import (
    analyze_fft_frequency, analyze_spatial_residuals, generate_heatmap_overlay,
    fast_cpu_heuristic_fallback, run_detection_pipeline
)
from services.report_manager import ReportManager


def create_synthetic_test_image(mode="synthetic") -> bytes:
    """Generates synthetic-like or camera-like test image in bytes."""
    width, height = 300, 300
    if mode == "synthetic":
        # Create image with high-frequency periodic grid / checkerboard artifacts
        img = PILImage.new("RGB", (width, height), color=(120, 120, 120))
        draw = ImageDraw.Draw(img)
        # Add high-frequency checkerboard / grid lines typical of deconvolution upsampling
        for x in range(0, width, 4):
            draw.line([(x, 0), (x, height)], fill=(180, 180, 180), width=1)
        for y in range(0, height, 4):
            draw.line([(0, y), (width, y)], fill=(180, 180, 180), width=1)
        buf = io.BytesIO()
        # Save as PNG with embedded AI prompt chunk
        png_info = PngImagePlugin.PngInfo()
        png_info.add_text("parameters", "photorealistic portrait, masterpiece, steps: 30, sampler: DPM++ 2M Karras, CFG: 7")
        img.save(buf, format="PNG", pnginfo=png_info)
        return buf.getvalue()
    else:
        # Create natural-looking photo with smooth gradient and realistic random sensor noise
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                # Smooth continuous gradient
                arr[y, x, 0] = int(255 * (x / width))
                arr[y, x, 1] = int(255 * (y / height))
                arr[y, x, 2] = int(128 + 60 * np.sin(x / 20.0))
        # Add simulated camera photon sensor noise (correlated across channels)
        sensor_noise = np.random.normal(0, 4.0, (height, width, 1))
        noisy_arr = np.clip(arr.astype(np.float32) + sensor_noise, 0, 255).astype(np.uint8)
        img = PILImage.fromarray(noisy_arr, mode="RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()


class TestAIImageDetectorSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_user_authentication_and_jwt(self):
        """Test User registration, login, guest session, and JWT claims."""
        test_email = f"analyst_{os.urandom(4).hex()}@forensic.ai"
        success, msg, res = AuthService.register("Dr. Jane Analyst", test_email, "SecurePass789!", role="user")
        self.assertTrue(success, f"Registration failed: {msg}")
        self.assertIn("token", res)
        self.assertEqual(res["user"]["role"], "user")

        # Test login
        login_success, login_msg, login_res = AuthService.login(test_email, "SecurePass789!")
        self.assertTrue(login_success, f"Login failed: {login_msg}")
        self.assertIn("token", login_res)

        # Test token decode
        decoded = AuthService.verify_token(login_res["token"])
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["email"], test_email)

        # Test Guest Session
        guest_res = AuthService.guest_session()
        self.assertIn("token", guest_res)
        self.assertTrue(guest_res["user"]["is_guest"])

    def test_02_image_validation_bounds_and_rejection(self):
        """Test validation of magic bytes, dimensions, and corrupt buffers."""
        img_model = ImageModel(None, None, "test.jpg", "image/jpeg")

        # 1. Empty buffer
        valid, err, _ = img_model.validate(b"")
        self.assertFalse(valid)
        self.assertIn("empty", err.lower())

        # 2. Corrupt buffer / invalid magic bytes
        valid, err, _ = img_model.validate(b"NOT_AN_IMAGE_HEADER_RANDOM_TEXT")
        self.assertFalse(valid)
        self.assertIn("magic bytes", err.lower())

        # 3. Valid synthetic image
        valid_bytes = create_synthetic_test_image("synthetic")
        valid, err, pil_img = img_model.validate(valid_bytes)
        self.assertTrue(valid, f"Validation failed on valid PNG: {err}")
        self.assertIsNotNone(pil_img)

    def test_03_dual_branch_inference_engine(self):
        """Test Branch A (FFT) and Branch B (Spatial) on synthetic vs natural imagery."""
        detector = AIImageDetector.get_default()

        # Synthetic image
        synth_bytes = create_synthetic_test_image("synthetic")
        synth_img = PILImage.open(io.BytesIO(synth_bytes))
        fft_synth, fft_metrics = analyze_fft_frequency(np.array(synth_img.convert("L")))
        spatial_synth, spatial_metrics, anomaly_map = analyze_spatial_residuals(synth_img)

        self.assertGreaterEqual(fft_synth, 0.0)
        self.assertLessEqual(fft_synth, 1.0)
        self.assertGreaterEqual(spatial_synth, 0.0)
        self.assertLessEqual(spatial_synth, 1.0)
        self.assertEqual(anomaly_map.shape, (300, 300))

        # Real photo-like image
        real_bytes = create_synthetic_test_image("natural")
        real_img = PILImage.open(io.BytesIO(real_bytes))
        fft_real, _ = analyze_fft_frequency(np.array(real_img.convert("L")))
        spatial_real, _, _ = analyze_spatial_residuals(real_img)

        # End-to-end pipeline run on synthetic
        heatmaps_dir = os.path.join(self.app.static_folder, "uploads", "heatmaps")
        test_image_record = ImageModel(None, None, "synth.png", "image/png")
        analysis_res = run_detection_pipeline(test_image_record, synth_bytes, heatmaps_dir, detector)

        self.assertIn("confidence_score", analysis_res)
        self.assertIn("heatmap_path", analysis_res)
        self.assertTrue(os.path.exists(analysis_res["heatmap_path"]), "Heatmap file was not written to disk.")
        # Generative metadata should be detected and confidence should exceed threshold 0.75
        self.assertGreater(analysis_res["confidence_score"], 0.75)
        self.assertEqual(detector.detect_ai(analysis_res["confidence_score"]), "Likely AI-Generated")

    def test_04_circuit_breaker_fallback(self):
        """Test CPU fast heuristic fallback under error conditions."""
        test_img = PILImage.new("RGB", (100, 100), color=(200, 100, 50))
        fft_score, spatial_score, confidence = fast_cpu_heuristic_fallback(test_img)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_05_pdf_and_json_report_generation(self):
        """Test ReportManager generating both PDF and JSON reports with academic disclaimer."""
        # Run scan via detector
        synth_bytes = create_synthetic_test_image("synthetic")
        uploads_dir = os.path.join(self.app.static_folder, "uploads", "originals")
        heatmaps_dir = os.path.join(self.app.static_folder, "uploads", "heatmaps")

        image_record = ImageModel(None, None, "evidence_test.png", "image/png")
        image_record.upload(uploads_dir, synth_bytes)

        detector = AIImageDetector.get_default()
        detection_result = detector.analyze_image(image_record, synth_bytes, heatmaps_dir)
        result_id = detection_result.result_id

        # 1. JSON Report
        json_report = ReportManager.generate_json_report(result_id)
        self.assertEqual(json_report["report_type"], "AI_IMAGE_FORENSIC_INSPECTION_CERTIFICATE")
        self.assertIn("disclaimer", json_report)
        self.assertIn("spectral_metrics", json_report)

        # 2. PDF Report
        pdf_filename, mime, pdf_bytes = ReportManager.download_report(result_id, report_format="pdf")
        self.assertEqual(mime, "application/pdf")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Generated PDF does not have valid %PDF magic header.")
        self.assertGreater(len(pdf_bytes), 1000, "PDF size is unusually small.")

    def test_06_flask_api_endpoints(self):
        """Test Flask HTTP API endpoints: /api/health, upload-and-analyze, result, history, admin."""
        # 1. Health check
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)

        # 2. Upload and analyze via API
        synth_bytes = create_synthetic_test_image("synthetic")
        data = {
            "image": (io.BytesIO(synth_bytes), "sample_ai_art.png")
        }
        res_upload = self.client.post("/api/detector/upload-and-analyze", data=data, content_type="multipart/form-data")
        self.assertEqual(res_upload.status_code, 200)
        json_data = res_upload.get_json()
        self.assertIn("result", json_data)
        result_id = json_data["result"]["result_id"]

        # 3. Fetch Result
        res_get = self.client.get(f"/api/detector/result/{result_id}")
        self.assertEqual(res_get.status_code, 200)

        # 4. Fetch History
        res_hist = self.client.get("/api/detector/history?search=sample_ai_art")
        self.assertEqual(res_hist.status_code, 200)
        hist_data = res_hist.get_json()
        self.assertGreater(hist_data["total"], 0)

        # 5. Fetch PDF Report via API
        res_pdf = self.client.get(f"/api/detector/report/{result_id}/pdf")
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, "application/pdf")

        # 6. Admin API (with Admin login token)
        login_res = self.client.post("/api/auth/login", json={
            "email": "admin@forensic.ai",
            "password": "AdminPass123!"
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.get_json()["token"]

        res_metrics = self.client.get("/api/admin/metrics", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_metrics.status_code, 200)
        metrics_data = res_metrics.get_json()
        self.assertIn("total_scans", metrics_data)
        self.assertIn("ai_scans", metrics_data)


if __name__ == "__main__":
    unittest.main()
