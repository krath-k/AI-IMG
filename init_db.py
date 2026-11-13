"""
init_db.py
Database schema initialization and seed script.
Seeds default administrator and analyst demo accounts.
"""

import sys
import os

# Add project root to Python module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db as initialize_tables, User, AuditLog


def seed_database():
    """Initializes tables and seeds default user credentials if not already present."""
    print("-> Initializing SQLite database schema...")
    initialize_tables()

    # Seed Admin User
    admin = User.get_by_email("admin@forensic.ai")
    if not admin:
        print("-> Seeding default Administrator account: admin@forensic.ai")
        admin = User.create(
            name="Forensic Chief Admin",
            email="admin@forensic.ai",
            password="AdminPass123!",
            role="admin"
        )
        AuditLog.record("SYSTEM_INIT", "Seeded Administrator account (admin@forensic.ai)", user_id=admin.user_id)
    else:
        print("-> Administrator account already exists.")

    # Seed Regular Demo Analyst
    demo_user = User.get_by_email("demo@forensic.ai")
    if not demo_user:
        print("-> Seeding default Analyst account: demo@forensic.ai")
        demo_user = User.create(
            name="Forensic Analyst Demo",
            email="demo@forensic.ai",
            password="DemoUser123!",
            role="user"
        )
        AuditLog.record("SYSTEM_INIT", "Seeded Demo Analyst account (demo@forensic.ai)", user_id=demo_user.user_id)
    else:
        print("-> Demo Analyst account already exists.")

    print("[SUCCESS] Database initialized and seeded successfully.")


if __name__ == "__main__":
    seed_database()
