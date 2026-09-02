"""
Seed script for Midda database.

Populates lookup tables with initial vocabulary:
- allergens (Kassal's 22 codes — must match their API exactly)
- nutrients (Kassal's 8 nutrition codes)
- diets (Norwegian dietary categories)
- tools (kitchen equipment)
- regions (cuisines)

Idempotent — safe to run multiple times. Only adds rows that don't exist.
Existing rows are never modified.

Usage:
    python seed.py

Reads DATABASE_URL from environment. Defaults to sqlite:///./midda.db.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from models import Allergen, Diet, Nutrient, Region, Tool


# ============================================================
# Seed data
# ============================================================

# Allergens: `code` matches Kassal's codes 1-to-1 so their allergen responses
# map cleanly during product ingest. Display names are Norwegian.
ALLERGENS: list[tuple[str, str]] = [
    # Mattilsynet's core 14
    ("melk", "Melk"),
    ("gluten", "Gluten"),
    ("egg", "Egg"),
    ("fisk", "Fisk"),
    ("skalldyr", "Skalldyr"),
    ("blotdyr", "Bløtdyr"),
    ("soya", "Soya"),
    ("selleri", "Selleri"),
    ("sennep", "Sennep"),
    ("sesam", "Sesam"),
    ("sulfitt", "Sulfitt"),
    ("lupiner", "Lupiner"),
    ("notter", "Nøtter"),
    ("peanotter", "Peanøtter"),
    # Nut sub-types Kassal reports separately
    ("hasselnott", "Hasselnøtter"),
    ("mandel", "Mandler"),
    ("pistasjnott", "Pistasjnøtter"),
    ("valnott", "Valnøtter"),
    ("cashewnott", "Cashewnøtter"),
    ("macadamianott", "Macadamianøtter"),
    ("paranott", "Paranøtter"),
    ("pekannott", "Pekannøtter"),
]

# Nutrients: `code` matches Kassal's nutrition codes.
# (code, display_name, default_unit)
NUTRIENTS: list[tuple[str, str, str]] = [
    ("energi_kcal", "Kalorier", "kcal"),
    ("energi_kj", "Energi", "kj"),
    ("fett_totalt", "Fett", "g"),
    ("mettet_fett", "Mettet fett", "g"),
    ("karbohydrater", "Karbohydrater", "g"),
    ("sukkerarter", "Sukkerarter", "g"),
    ("protein", "Protein", "g"),
    ("salt", "Salt", "g"),
]

# Diets: starter set. Expand via a new seed run when needed.
DIETS: list[str] = [
    "Vegetar",
    "Vegansk",
    "Pescetariansk",
    "Glutenfri",
    "Laktosefri",
    "Melkefri",
    "Nøttefri",
    "Lavkarbo",
    "Halal",
    "Kosher",
]

# Tools: common Norwegian kitchen equipment. Grow as recipes reveal gaps.
TOOLS: list[str] = [
    "Stekepanne",
    "Gryte",
    "Kasserolle",
    "Ovn",
    "Stavmikser",
    "Kjøkkenmaskin",
    "Foodprocessor",
    "Blender",
    "Wok",
    "Trykkoker",
    "Slow cooker",
    "Mikrobølgeovn",
    "Vaffeljern",
    "Rivjern",
    "Visp",
    "Bakebolle",
    "Sil",
    "Skjærebrett",
    "Grill",
    "Kjøkkenvekt",
    "Airfryer",
]

# Regions: cuisines. Kept moderate — expand as content grows.
REGIONS: list[str] = [
    "Norsk",
    "Nordisk",
    "Italiensk",
    "Fransk",
    "Spansk",
    "Gresk",
    "Tyrkisk",
    "Marokkansk",
    "Midtøstlig",
    "Indisk",
    "Thai",
    "Vietnamesisk",
    "Kinesisk",
    "Japansk",
    "Koreansk",
    "Meksikansk",
    "Amerikansk",
]


# ============================================================
# Idempotent inserts
# ============================================================

def seed_allergens(session: Session) -> int:
    existing = set(session.execute(select(Allergen.code)).scalars().all())
    added = 0
    for code, display_name in ALLERGENS:
        if code not in existing:
            session.add(Allergen(code=code, display_name=display_name))
            added += 1
    return added


def seed_nutrients(session: Session) -> int:
    existing = set(session.execute(select(Nutrient.code)).scalars().all())
    added = 0
    for code, display_name, default_unit in NUTRIENTS:
        if code not in existing:
            session.add(
                Nutrient(
                    code=code,
                    display_name=display_name,
                    default_unit=default_unit,
                )
            )
            added += 1
    return added


def seed_named_lookup(session: Session, model, names: list[str]) -> int:
    """Generic seeder for lookup tables keyed on a unique `name` column."""
    existing = set(session.execute(select(model.name)).scalars().all())
    added = 0
    for name in names:
        if name not in existing:
            session.add(model(name=name))
            added += 1
    return added


# ============================================================
# Main
# ============================================================

def main() -> None:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./midda.db")
    engine = create_engine(database_url)

    print(f"Seeding database: {database_url}")

    with Session(engine) as session:
        # SQLite needs FK enforcement enabled per connection.
        # Harmless on Postgres — no-op if the pragma isn't recognised.
        if database_url.startswith("sqlite"):
            session.execute(text("PRAGMA foreign_keys = ON"))

        added_allergens = seed_allergens(session)
        added_nutrients = seed_nutrients(session)
        added_diets = seed_named_lookup(session, Diet, DIETS)
        added_tools = seed_named_lookup(session, Tool, TOOLS)
        added_regions = seed_named_lookup(session, Region, REGIONS)

        session.commit()

    print(
        f"Added: allergens={added_allergens}, nutrients={added_nutrients}, "
        f"diets={added_diets}, tools={added_tools}, regions={added_regions}"
    )
    print("Done.")


if __name__ == "__main__":
    main()