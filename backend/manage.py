"""
BioTime Open — Management CLI.
Usage:
  python manage.py seed          # Seed device models + first admin
  python manage.py create-superuser
"""
import asyncio
import sys

from core.database import load_models

# Make sure every table (and its foreign keys) is registered before any
# command touches the database.
load_models()


async def seed():
    from core.database import AsyncSessionLocal
    from core.seed import run_seed
    async with AsyncSessionLocal() as db:
        await run_seed(db)
    print("Seed completed.")


async def create_superuser():
    import getpass
    from core.database import AsyncSessionLocal
    from core.auth.service import create_user

    email = input("Email: ")
    password = getpass.getpass("Password: ")
    async with AsyncSessionLocal() as db:
        user = await create_user(db, email=email, password=password, role="super_admin")
        print(f"Superuser created: {user.email}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "seed":
        asyncio.run(seed())
    elif cmd == "create-superuser":
        asyncio.run(create_superuser())
    else:
        print(__doc__)
