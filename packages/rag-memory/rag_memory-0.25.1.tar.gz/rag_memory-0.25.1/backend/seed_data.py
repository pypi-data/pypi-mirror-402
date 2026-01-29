#!/usr/bin/env python3
"""Database seed script - populates initial data.

Idempotent - can be run multiple times safely.
Safe to re-run after dropping data.

Usage:
    python seed_data.py              # Seed all data
    python seed_data.py --clear      # Clear and re-seed
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.database import async_session_maker
from app.rag.models import StarterPrompt


STARTER_PROMPTS = [
    {
        "prompt_text": "What collections do I have?",
        "category": "exploration",
        "has_placeholder": False,
        "display_order": 1,
    },
    {
        "prompt_text": "Search my knowledge base for [topic]",
        "category": "search",
        "has_placeholder": True,
        "display_order": 2,
    },
    {
        "prompt_text": "Show me what's in the [collection name] collection",
        "category": "exploration",
        "has_placeholder": True,
        "display_order": 3,
    },
    {
        "prompt_text": "What topics are covered in my knowledge base?",
        "category": "exploration",
        "has_placeholder": False,
        "display_order": 4,
    },
    {
        "prompt_text": "How has my understanding of [topic] evolved?",
        "category": "analysis",
        "has_placeholder": True,
        "display_order": 5,
    },
    {
        "prompt_text": "What's the relationship between [concept A] and [concept B]?",
        "category": "analysis",
        "has_placeholder": True,
        "display_order": 6,
    },
    {
        "prompt_text": "What's new about [topic] that I might not know yet?",
        "category": "analysis",
        "has_placeholder": True,
        "display_order": 7,
    },
]


async def seed_starter_prompts(clear: bool = False):
    """Seed starter prompts (idempotent)."""
    async with async_session_maker() as db:
        # Clear if requested
        if clear:
            result = await db.execute(select(StarterPrompt))
            existing = result.scalars().all()
            if existing:
                print(f"🗑️  Clearing {len(existing)} existing starter prompts...")
                for prompt in existing:
                    await db.delete(prompt)
                await db.commit()
                print("  ✓ Cleared")

        # Check if prompts exist
        result = await db.execute(select(StarterPrompt))
        existing = result.scalars().all()

        if existing and not clear:
            print(f"✓ Starter prompts already exist ({len(existing)} found) - skipping")
            return

        # Insert prompts
        print(f"📝 Seeding {len(STARTER_PROMPTS)} starter prompts...")
        for prompt_data in STARTER_PROMPTS:
            prompt = StarterPrompt(**prompt_data)
            db.add(prompt)

        await db.commit()
        print(f"✓ Successfully seeded {len(STARTER_PROMPTS)} starter prompts")


async def seed_all(clear: bool = False):
    """Seed all data."""
    print("🌱 Seeding database...")
    await seed_starter_prompts(clear=clear)
    print("✓ Database seeding complete")


def main():
    parser = argparse.ArgumentParser(description="Seed database with initial data")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding",
    )
    args = parser.parse_args()

    asyncio.run(seed_all(clear=args.clear))


if __name__ == "__main__":
    main()
