"""
Migration script to update employee_id column from varchar(5) to varchar(6).
Run this once to fix the database schema.
"""
import asyncio
import asyncpg


async def main():
    # Connect to database
    conn = await asyncpg.connect(
        user="erp_user",
        password="erp_password",
        database="erp_db",
        host="localhost",
        port=5432,
    )
    
    try:
        # Alter column to varchar(6)
        await conn.execute("""
            ALTER TABLE employees 
            ALTER COLUMN employee_id TYPE VARCHAR(6);
        """)
        print("Successfully updated employee_id column to VARCHAR(6)")
        
        # Verify
        result = await conn.fetchrow("""
            SELECT column_name, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'employees' AND column_name = 'employee_id';
        """)
        print(f"Verified: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

