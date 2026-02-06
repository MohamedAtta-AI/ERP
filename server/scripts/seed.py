import sys
import os
import traceback
from datetime import date

# Add project root to path so we can import 'server'
sys.path.append(os.getcwd())

from sqlmodel import Session, select
from server.db import engine
from server.db.models import Person, Role, PersonStatus
from server.app.services.password_service import hash_password


def seed():
    print("Seeding database...")
    try:
        with Session(engine) as session:
            # Admin
            admin = session.get(Person, "ADMIN1")
            if not admin:
                print("Creating Admin (ADMIN1)...")
                admin = Person(
                    id="ADMIN1",
                    full_name="System Admin",
                    email="admin@ontime.com",
                    phone="0000000000",
                    role=Role.ADMIN,
                    status=PersonStatus.ACTIVE,
                    password_hash=hash_password("admin123"),
                    nationalID="11111111111111",
                    hire_date=date.today(),  # Add this
                )
                session.add(admin)
            else:
                print("Admin already exists.")

            # Supervisor
            sup = session.get(Person, "SUP001")
            if not sup:
                print("Creating Supervisor (SUP001)...")
                sup = Person(
                    id="SUP001",
                    full_name="Site Supervisor",
                    email="supervisor@ontime.com",
                    phone="0000000001",
                    role=Role.SUPERVISOR,
                    status=PersonStatus.ACTIVE,
                    password_hash=hash_password("supervisor123"),
                    nationalID="22222222222222",
                    hire_date=date.today(),  # Add this
                )
                session.add(sup)
            else:
                print("Supervisor already exists.")

            session.commit()
            print("Seeding complete!")

    except Exception as e:
        print(f"Error during seeding: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    seed()
