# SpectraForensics AI Image Detector System

An enterprise-grade, modular web application and forensic intelligence platform for detecting AI-generated and synthetic imagery (Stable Diffusion, Midjourney, DALL-E, Flux, GANs, and Latent Diffusion models) using dual-branch frequency-domain FFT power spectrum analysis, spatial noise residual analysis, and deep provenance metadata extraction.

---

## Architecture Overview (3-Tier Forensic System)

```
AI-IMG/
├── app.py                      # Application entrypoint & Flask factory
├── init_db.py                  # Database schema initialization and seed script
├── test_system.py              # Automated unit and integration test suite
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation & setup guide
├── python.bat / run.bat        # Zero-config execution launcher scripts
├── models/
│   ├── __init__.py
│   └── database.py             # SQLite ORM models: User, Image, AIImageDetector,
│                               # DetectionResult, Report, and AuditLog
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # JWT session management, RBAC, and guest access
│   ├── detection_engine.py     # Dual-branch FFT & spatial engine + circuit breaker
│   └── report_manager.py       # PDF/JSON certificate generator & audit analytics
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py          # /api/auth endpoints (register, login, guest, profile)
│   ├── detector_routes.py      # /api/detector endpoints (upload, result, history, reports)
│   └── admin_routes.py         # /api/admin endpoints (metrics, audit logs, circuit breaker)
└── frontend/
    ├── templates/
    │   └── index.html          # Dark-mode single-page forensic workspace
    └── static/
        ├── css/
        │   └── style.css       # Dark cyber-forensic design system
        ├── js/
        │   └── app.js          # Interactive UI state, split slider, and API client
        └── uploads/
            ├── originals/      # Evidence image storage
            └── heatmaps/       # Generated Jet colormap artifact overlays
```

---

## Core Forensic Capabilities

### 1. Dual-Branch Detection Pipeline (Fork/Join)
* **Branch A — Frequency-Domain 2D FFT Analysis:**
  Computes the 2D Fast Fourier Transform on the evidence image, applying radial power spectrum profile fitting. Generative upsampling and transposed convolution decoders produce characteristic high-frequency grid spikes and unnatural energy inflation that depart from natural $P(f) \propto 1/f^{\alpha}$ scene physics.
* **Branch B — Spatial Feature & Noise Residual Analysis:**
  Extracts high-pass noise residuals via 2D Laplacian filtering. Evaluates physical camera sensor noise patterns (PRNU and photon shot noise with Bayer CFA inter-channel correlation) versus synthetic latent denoising uniformity and kurtosis anomalies.
* **Visual Artifact Heatmap Inspector:**
  Generates a continuous Jet/Turbo colormap overlay highlighting localized generative anomalies. Features an interactive **before/after split slider**, view mode toggles (Original, Heatmap, Blend), and live opacity control.

### 2. Fault-Tolerant Circuit Breaker Fallback
If the primary multi-spectral inference pipeline encounters resource constraints, memory pressure, or unexpected exceptions, an automated circuit breaker immediately diverts execution to a fast CPU heuristic engine, records the incident in the system audit log, and badges the output with an advisory fallback tag without interrupting user workflow.

### 3. Deep Provenance & Prompt Chunk Inspection
Deep scans EXIF tags and PNG metadata chunks (`parameters`, `prompt`, `workflow`, `Software: Automatic1111`, `ComfyUI`, `Midjourney`, etc.) to detect explicit generative prompts and model watermarks.

### 4. Forensic Report Generation
Exports formal forensic verification certificates in two formats:
* **JSON:** Standardized machine-readable diagnostic schema with SHA-256 hashes, timestamps, and metric breakdowns.
* **PDF:** Certified document rendered via ReportLab with color-coded verdict banners, score tables, embedded side-by-side evidence and heatmap graphics, and the academic forensic disclaimer.

---

## Default Credentials & Demo Access

The system initializes automatically on first run and seeds the following demonstration accounts:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@forensic.ai` | `AdminPass123!` | Full access to Detection Workspace, Scan History, and Admin Audit Panel |
| **Analyst Demo** | `demo@forensic.ai` | `DemoUser123!` | Standard access to Detection Workspace and user scan history |
| **Guest Analyst** | *Instant 1-Click* | *None required* | Frictionless testing without registration via "Continue as Guest" |

---

## Quick Start & Installation

### Option 1: Direct Execution (Windows / Cross-Platform)
```bash
# 1. Activate the included virtual environment
.\venv\Scripts\activate

# 2. Run the application
python app.py
```

Or execute the provided batch launcher:
```cmd
run.bat
```

### Option 2: Clean Environment Setup
```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database and seed default accounts
python init_db.py

# 5. Launch the application
python app.py
```

The web application will be live at:
**`http://127.0.0.1:5000`**

---

## Automated Test Suite

Run the full integration test suite covering authentication, image validation bounds, dual-branch inference, heatmap generation, circuit breaker fallback, PDF/JSON export, and REST endpoints:

```bash
.\venv\Scripts\python.exe test_system.py
```

Expected result:
```
Ran 6 tests in 1.24s
OK
```

---

## API Reference Summary

### Authentication (`/api/auth`)
* `POST /api/auth/register` - Create a new user account.
* `POST /api/auth/login` - Authenticate credentials and receive JWT session.
* `POST /api/auth/guest` - Generate an immediate guest demonstration session.
* `GET  /api/auth/me` - Retrieve current session claims.
* `POST /api/auth/logout` - Clear user session.

### Forensic Detection (`/api/detector`)
* `POST /api/detector/upload-and-analyze` - Upload image (`JPG`/`PNG`, max 25MB, max 8192x8192) for dual-branch analysis.
* `GET  /api/detector/result/<result_id>` - Retrieve serialized detection result and metrics.
* `GET  /api/detector/history` - Query past scans with search, verdict, and confidence filters.
* `GET  /api/detector/report/<result_id>/pdf` - Download formal PDF forensic certificate.
* `GET  /api/detector/report/<result_id>/json` - Download structured JSON diagnostic payload.

### Administrator Audit (`/api/admin`)
* `GET /api/admin/metrics` - Retrieve total verifications, detection distribution ratios, and fallback rates.
* `GET /api/admin/audit-logs` - Inspect chronological operational and security audit feed.
* `GET /api/admin/circuit-breaker-logs` - Inspect circuit breaker trigger events.

---

## Academic Disclaimer
*This system provides algorithmic probability estimates based on frequency-domain spectra and noise residual patterns. It is not a definitive legal or forensic conclusion. Forensic analysts should corroborate findings with device hardware provenance, raw sensor dump analysis, and chain-of-custody documentation.*
