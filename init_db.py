import asyncio
import sys
import os

# Add backend/app to path
sys.path.append(os.path.abspath("backend/app"))

from db.session import init_db

async def main():
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())
