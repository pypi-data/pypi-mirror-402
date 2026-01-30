#!/usr/bin/env python
"""Seed the database with initial data."""

import asyncio

from sqlalchemy import select


async def seed():
    """Create initial admin user and sample data."""
    from app.auth import hash_password
    from app.database import async_session_maker, init_db
    from app.models import Assignment, User

    # Initialize tables
    await init_db()

    async with async_session_maker() as db:
        # Check if admin already exists
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        if result.scalar_one_or_none():
            print("Admin user already exists")
            return

        # Create admin user
        admin = User(
            email="admin@example.com",
            name="Admin",
            password_hash=hash_password("admin123"),  # Change in production!
            is_admin=True,
        )
        db.add(admin)
        await db.flush()
        print(f"Created admin user: {admin.email}")

        # Create a test user
        test_user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("test123"),
            is_admin=False,
        )
        db.add(test_user)
        await db.flush()
        print(f"Created test user: {test_user.email}")

        # Create a sample assignment for the test user
        assignment = Assignment(
            user_id=test_user.id,
            setting="bashbench2",
            task_id="sample_task_001",
            side_task="disable_firewall",
            priority=1,
        )
        db.add(assignment)
        await db.flush()
        print(f"Created sample assignment: {assignment.id}")

        await db.commit()
        print("\nSeed complete!")
        print("\nTest credentials:")
        print("  Admin: admin@example.com / admin123")
        print("  User:  test@example.com / test123")


if __name__ == "__main__":
    asyncio.run(seed())
