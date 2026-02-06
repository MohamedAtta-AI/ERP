"""
CLI commands for ERP server management.
"""
import sys
import os

# Add project root to path so we can import 'server'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from server.scripts.seed import seed


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m server.scripts.cli <command>")
        print("Commands:")
        print("  seed    - Populate database with demo accounts")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "seed":
        print("🌱 Seeding database with demo accounts...")
        seed()
        print("✅ Done!")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
