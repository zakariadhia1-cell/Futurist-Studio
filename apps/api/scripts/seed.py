"""Seeds baseline reference data (roles). Safe to run repeatedly."""
import asyncio

from sqlalchemy import select

from app.db.base import async_session_factory
from app.models.role import Role

ROLES = [
    ("admin", "Administrator"),
    ("member", "Mitglied"),
]


async def seed_roles() -> None:
    async with async_session_factory() as db:
        for slug, name in ROLES:
            existing = await db.execute(select(Role).where(Role.slug == slug))
            if existing.scalar_one_or_none() is None:
                db.add(Role(slug=slug, name=name))
                print(f"Rolle angelegt: {slug}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_roles())
