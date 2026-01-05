"""
Seed script for OnTime ERP database.

Creates initial data:
- Roles (admin, supervisor, worker)
- Admin user
- Supervisor user
- Sample workers
- Locations
- Shifts
- Skills
- Salary components
- Assignments
- Sample attendance records
"""

import asyncio
from datetime import date, time, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from server.config import config
from server.db.models import (
    Role, Person, Location, Shift, Skill,
    SalaryComponent, ComponentKind, ComponentType, AmountType,
    Assignment, Attendance, AttendanceStatus,
    PayrollPeriod, PayrollPeriodStatus,
)


async def seed_database():
    """Seed the database with initial data."""
    from sqlmodel import select
    
    engine = create_async_engine(config.DB_URL, echo=True)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Create or get roles
        print("Creating roles...")
        
        # Check for existing roles
        existing_roles = (await session.execute(select(Role))).scalars().all()
        role_by_name = {r.name: r for r in existing_roles}
        
        if "admin" in role_by_name:
            admin_role = role_by_name["admin"]
            print("  ✓ Admin role already exists")
        else:
            admin_role = Role(id=uuid4(), name="admin", description="Administrator with full access")
            session.add(admin_role)
            
        if "supervisor" in role_by_name:
            supervisor_role = role_by_name["supervisor"]
            print("  ✓ Supervisor role already exists")
        else:
            supervisor_role = Role(id=uuid4(), name="supervisor", description="Supervisor/Employee with limited access")
            session.add(supervisor_role)
            
        if "worker" in role_by_name:
            worker_role = role_by_name["worker"]
            print("  ✓ Worker role already exists")
        else:
            worker_role = Role(id=uuid4(), name="worker", description="Worker with read-only access")
            session.add(worker_role)
        
        await session.flush()
        print(f"✅ Roles ready: admin, supervisor, worker")
        
        # Create or get locations
        print("Creating locations...")
        existing_locations = (await session.execute(select(Location))).scalars().all()
        loc_by_name = {l.name: l for l in existing_locations}
        
        if "Main Construction Site" in loc_by_name:
            location_main = loc_by_name["Main Construction Site"]
        else:
            location_main = Location(
                id=uuid4(),
                name="Main Construction Site",
                city="New York",
                address="123 Main St, New York, NY",
            )
            session.add(location_main)
            
        if "Secondary Site" in loc_by_name:
            location_secondary = loc_by_name["Secondary Site"]
        else:
            location_secondary = Location(
                id=uuid4(),
                name="Secondary Site",
                city="Brooklyn",
                address="456 Oak Ave, Brooklyn, NY",
            )
            session.add(location_secondary)
            
        if "Warehouse" in loc_by_name:
            location_warehouse = loc_by_name["Warehouse"]
        else:
            location_warehouse = Location(
                id=uuid4(),
                name="Warehouse",
                city="Queens",
                address="789 Industrial Rd, Queens, NY",
            )
            session.add(location_warehouse)
        
        locations = [location_main, location_secondary, location_warehouse]
        await session.flush()
        print(f"✅ Locations ready")
        
        # Create or get shifts
        print("Creating shifts...")
        existing_shifts = (await session.execute(select(Shift))).scalars().all()
        shift_by_name = {s.name: s for s in existing_shifts}
        
        if "Morning Shift" in shift_by_name:
            shift_morning = shift_by_name["Morning Shift"]
        else:
            shift_morning = Shift(
                id=uuid4(),
                name="Morning Shift",
                starts_at=time(8, 0),
                ends_at=time(17, 0),
            )
            session.add(shift_morning)
            
        if "Afternoon Shift" in shift_by_name:
            shift_afternoon = shift_by_name["Afternoon Shift"]
        else:
            shift_afternoon = Shift(
                id=uuid4(),
                name="Afternoon Shift",
                starts_at=time(13, 0),
                ends_at=time(22, 0),
            )
            session.add(shift_afternoon)
            
        if "Night Shift" in shift_by_name:
            shift_night = shift_by_name["Night Shift"]
        else:
            shift_night = Shift(
                id=uuid4(),
                name="Night Shift",
                starts_at=time(22, 0),
                ends_at=time(6, 0),
                is_overnight=True,
            )
            session.add(shift_night)
        
        shifts = [shift_morning, shift_afternoon, shift_night]
        await session.flush()
        print(f"✅ Shifts ready")
        
        # Create or get admin person
        print("Creating admin user...")
        existing_admin = (await session.execute(select(Person).where(Person.id == "ADMIN1"))).scalar_one_or_none()
        if existing_admin:
            admin_person = existing_admin
            print(f"  ✓ Admin already exists: {admin_person.id}")
        else:
            admin_person = Person(
                id="ADMIN1",
                full_name="System Administrator",
                email="admin@ontime-erp.com",
                role_id=admin_role.id,
                status="active",
                department="Administration",
                position="System Admin",
            )
            session.add(admin_person)
            await session.flush()
            print(f"✅ Created admin: {admin_person.id}")
        
        # Create or get supervisor person
        print("Creating supervisor user...")
        existing_supervisor = (await session.execute(select(Person).where(Person.id == "SUPER1"))).scalar_one_or_none()
        if existing_supervisor:
            supervisor_person = existing_supervisor
            print(f"  ✓ Supervisor already exists: {supervisor_person.id}")
        else:
            supervisor_person = Person(
                id="SUPER1",
                full_name="John Supervisor",
                email="supervisor@ontime-erp.com",
                role_id=supervisor_role.id,
                status="active",
                department="Operations",
                position="Site Supervisor",
            )
            session.add(supervisor_person)
            await session.flush()
            print(f"✅ Created supervisor: {supervisor_person.id}")
        
        # Create or get sample workers
        print("Creating sample workers...")
        workers_data = [
            ("WORK01", "Alice Johnson", "alice@ontime-erp.com", "Construction", "Carpenter"),
            ("WORK02", "Bob Smith", "bob@ontime-erp.com", "Construction", "Laborer"),
            ("WORK03", "Charlie Brown", "charlie@ontime-erp.com", "Maintenance", "Electrician"),
            ("WORK04", "Diana Davis", "diana@ontime-erp.com", "Construction", "Welder"),
            ("WORK05", "Edward Wilson", "edward@ontime-erp.com", "Logistics", "Driver"),
        ]
        
        workers = []
        for worker_id, name, email, dept, position in workers_data:
            existing_worker = (await session.execute(select(Person).where(Person.id == worker_id))).scalar_one_or_none()
            if existing_worker:
                workers.append(existing_worker)
            else:
                worker = Person(
                    id=worker_id,
                    full_name=name,
                    email=email,
                    role_id=worker_role.id,
                    supervisor_id=supervisor_person.id,
                    status="active",
                    department=dept,
                    position=position,
                )
                workers.append(worker)
                session.add(worker)
        
        await session.flush()
        print(f"✅ Workers ready: {len(workers)} workers")
        
        # Create or get skills
        print("Creating skills...")
        existing_skills = (await session.execute(select(Skill))).scalars().all()
        skill_by_name = {s.name: s for s in existing_skills}
        
        skill_data = [
            ("Carpentry", "Woodworking and framing"),
            ("Electrical", "Electrical systems installation"),
            ("Plumbing", "Plumbing installation and repair"),
            ("Welding", "Metal welding and fabrication"),
            ("Forklift Operation", "Certified forklift operator"),
            ("First Aid", "First aid certified"),
        ]
        
        skills = []
        for name, desc in skill_data:
            if name in skill_by_name:
                skills.append(skill_by_name[name])
            else:
                skill = Skill(id=uuid4(), name=name, description=desc)
                skills.append(skill)
                session.add(skill)
        
        await session.flush()
        print(f"✅ Skills ready: {len(skills)} skills")
        
        # Create or get salary components
        print("Creating salary components...")
        existing_components = (await session.execute(select(SalaryComponent))).scalars().all()
        comp_by_name = {c.name: c for c in existing_components}
        
        if "Base Salary" in comp_by_name:
            base_salary = comp_by_name["Base Salary"]
        else:
            base_salary = SalaryComponent(
                id=uuid4(),
                name="Base Salary",
                kind=ComponentKind.EARNING,
                type=ComponentType.BASE_SALARY,
                amount_type=AmountType.PER_DAY,
                amount=100.0,
                description="Daily base salary",
            )
            session.add(base_salary)
            
        if "Overtime Pay" in comp_by_name:
            overtime_pay = comp_by_name["Overtime Pay"]
        else:
            overtime_pay = SalaryComponent(
                id=uuid4(),
                name="Overtime Pay",
                kind=ComponentKind.EARNING,
                type=ComponentType.OVERTIME,
                amount_type=AmountType.PER_HOUR,
                amount=15.0,
                description="Overtime hourly rate (1.5x base)",
            )
            session.add(overtime_pay)
            
        if "Transportation Allowance" in comp_by_name:
            transport_allowance = comp_by_name["Transportation Allowance"]
        else:
            transport_allowance = SalaryComponent(
                id=uuid4(),
                name="Transportation Allowance",
                kind=ComponentKind.EARNING,
                type=ComponentType.ALLOWANCE,
                amount_type=AmountType.FIXED,
                amount=50.0,
                description="Monthly transportation allowance",
            )
            session.add(transport_allowance)
            
        if "Meal Allowance" in comp_by_name:
            meal_allowance = comp_by_name["Meal Allowance"]
        else:
            meal_allowance = SalaryComponent(
                id=uuid4(),
                name="Meal Allowance",
                kind=ComponentKind.EARNING,
                type=ComponentType.ALLOWANCE,
                amount_type=AmountType.PER_DAY,
                amount=10.0,
                description="Daily meal allowance",
            )
            session.add(meal_allowance)
            
        if "Tax Deduction" in comp_by_name:
            tax_deduction = comp_by_name["Tax Deduction"]
        else:
            tax_deduction = SalaryComponent(
                id=uuid4(),
                name="Tax Deduction",
                kind=ComponentKind.DEDUCTION,
                type=ComponentType.TAX,
                amount_type=AmountType.PERCENTAGE,
                amount=10.0,
                description="Income tax (10%)",
            )
            session.add(tax_deduction)
            
        if "Health Insurance" in comp_by_name:
            insurance_deduction = comp_by_name["Health Insurance"]
        else:
            insurance_deduction = SalaryComponent(
                id=uuid4(),
                name="Health Insurance",
                kind=ComponentKind.DEDUCTION,
                type=ComponentType.OTHER,
                amount_type=AmountType.FIXED,
                amount=25.0,
                description="Health insurance premium",
            )
            session.add(insurance_deduction)
            
        components = [base_salary, overtime_pay, transport_allowance, 
                      meal_allowance, tax_deduction, insurance_deduction]
        await session.flush()
        print(f"✅ Salary components ready")
        
        # Create assignments for all workers (skip if already exists)
        print("Creating assignments...")
        existing_assignments = (await session.execute(select(Assignment))).scalars().all()
        assigned_person_ids = {a.person_id for a in existing_assignments}
        
        today = date.today()
        created_count = 0
        
        # Supervisor assignment
        if supervisor_person.id not in assigned_person_ids:
            session.add(Assignment(
                id=uuid4(),
                person_id=supervisor_person.id,
                location_id=location_main.id,
                shift_id=shift_morning.id,
                title="Site Supervisor",
                rate=20.0,
                effective_from=today,
                is_active=True,
            ))
            created_count += 1
        
        # Worker assignments
        worker_assignments = [
            (workers[0].id, location_main.id, shift_morning.id, "Carpenter", 15.0),
            (workers[1].id, location_main.id, shift_morning.id, "Laborer", 12.0),
            (workers[2].id, location_secondary.id, shift_afternoon.id, "Electrician", 18.0),
            (workers[3].id, location_main.id, shift_morning.id, "Welder", 16.0),
            (workers[4].id, location_warehouse.id, shift_morning.id, "Warehouse Driver", 14.0),
        ]
        
        for person_id, loc_id, shift_id, title, rate in worker_assignments:
            if person_id not in assigned_person_ids:
                session.add(Assignment(
                    id=uuid4(),
                    person_id=person_id,
                    location_id=loc_id,
                    shift_id=shift_id,
                    title=title,
                    rate=rate,
                    effective_from=today,
                    is_active=True,
                ))
                created_count += 1
        
        await session.flush()
        print(f"✅ Assignments ready (created {created_count} new)")
        
        # Create sample attendance records for the past week (skip existing)
        print("Creating sample attendance records...")
        existing_attendance = (await session.execute(select(Attendance))).scalars().all()
        attendance_keys = {(a.person_id, a.attendance_date) for a in existing_attendance}
        
        created_count = 0
        for days_ago in range(7, 0, -1):
            attendance_date = today - timedelta(days=days_ago)
            # Skip weekends
            if attendance_date.weekday() >= 5:
                continue
                
            # Create attendance for each worker
            for worker in workers[:4]:  # First 4 workers have attendance
                if (worker.id, attendance_date) not in attendance_keys:
                    check_in_time = datetime.combine(attendance_date, time(8, 0)) + timedelta(minutes=int((hash(worker.id) % 30) - 15))
                    check_out_time = datetime.combine(attendance_date, time(17, 0)) + timedelta(minutes=int((hash(worker.id + "out") % 60) - 30))
                    
                    session.add(Attendance(
                        id=uuid4(),
                        person_id=worker.id,
                        location_id=location_main.id,
                        shift_id=shift_morning.id,
                        attendance_date=attendance_date,
                        check_in=check_in_time,
                        check_out=check_out_time,
                        status=AttendanceStatus.PRESENT,
                    ))
                    created_count += 1
        
        await session.flush()
        print(f"✅ Attendance records ready (created {created_count} new)")
        
        # Create a payroll period (if not exists)
        print("Creating payroll period...")
        month_start = date(today.year, today.month, 1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        existing_period = (await session.execute(
            select(PayrollPeriod).where(
                PayrollPeriod.start_date == month_start,
                PayrollPeriod.end_date == month_end
            )
        )).scalar_one_or_none()
        
        if existing_period:
            print(f"  ✓ Payroll period already exists: {month_start} to {month_end}")
        else:
            payroll_period = PayrollPeriod(
                id=uuid4(),
                start_date=month_start,
                end_date=month_end,
                status=PayrollPeriodStatus.OPEN,
            )
            session.add(payroll_period)
            await session.flush()
            print(f"✅ Created payroll period: {month_start} to {month_end}")
        
        await session.commit()
        print("\n" + "="*50)
        print("✅ Database seeded successfully!")
        print("="*50)
        print("\nCreated accounts:")
        print(f"  Admin:      ADMIN1 (admin@ontime-erp.com)")
        print(f"  Supervisor: SUPER1 (supervisor@ontime-erp.com)")
        print(f"  Workers:    WORK01, WORK02, WORK03, WORK04, WORK05")
        print("\nNote: Use the Admin or Supervisor ID to log in.")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())

