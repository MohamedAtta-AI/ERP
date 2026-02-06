#!/usr/bin/env python3
"""
Simple script to seed the database with demo accounts.
Run this from the project root: python seed_db.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from server.scripts.seed import seed

if __name__ == "__main__":
    print("🌱 Seeding database with demo accounts...")
    print("=" * 50)
    seed()
    print("=" * 50)
    print("✅ Database seeding complete!")
    print("\nDemo accounts created:")
    print("  - ADMIN1 / admin123 (Admin)")
    print("  - SUP001 / supervisor123 (Supervisor)")
    print("  - WRK001 / worker123 (Worker)")
