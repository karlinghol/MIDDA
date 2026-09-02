"""
SQLAlchemy models for Midda.

Everything lives in one file for now. Split by domain (dishes, ingredients,
products, lookups) when navigating this file starts to feel slow.

Design notes:
- All FKs from junction tables to their parent ("owning") side use
  ON DELETE CASCADE — deleting a dish should remove its ingredient rows.
- All FKs to lookup tables use ON DELETE RESTRICT — you shouldn't be able
  to delete an ingredient or allergen that's still referenced somewhere.
- Enums use native_enum=False so SQLite and PostgreSQL behave the same way
  (CHECK constraint in both cases). Changing enum values becomes a normal
  Alembic migration instead of an ALTER TYPE dance in Postgres.
- Timestamps use timezone=True from the start. SQLite ignores it, PostgreSQL
  respects it — retrofitting later is painful.
- Nutritional totals on Dish are denormalised (a snapshot). They can be
  recomputed from ingredients × products × qty when recipes change.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared base class for all ORM models."""
    pass


# ============================================================
# Enums
# ============================================================

class MeasurementType(str, Enum):
    WEIGHT = "weight"
    VOLUME = "volume"
    COUNT = "count"


class AllergenPresence(str, Enum):
    YES = "YES"
    NO = "NO"
    CAN_CONTAIN_TRACES = "CAN_CONTAIN_TRACES"


# ============================================================
# Lookup tables
# ============================================================

class Allergen(Base):
    __tablename__ = "allergens"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)


class Nutrient(Base):
    __tablename__ = "nutrients"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    default_unit: Mapped[str] = mapped_column(String(10), nullable=False)


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class Diet(Base):
    __tablename__ = "diets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


# ============================================================
# Products domain
# ============================================================

class Product(Base):
    __tablename__ = "products"

    ean: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100))
    image_url: Mapped[str | None] = mapped_column(String(500))
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    allergens: Mapped[list["ProductAllergen"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    nutrition: Mapped[list["ProductNutrition"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductAllergen(Base):
    __tablename__ = "product_allergens"

    product_ean: Mapped[str] = mapped_column(
        ForeignKey("products.ean", ondelete="CASCADE"), primary_key=True
    )
    allergen_code: Mapped[str] = mapped_column(
        ForeignKey("allergens.code", ondelete="RESTRICT"), primary_key=True
    )
    contains: Mapped[AllergenPresence] = mapped_column(
        SQLEnum(AllergenPresence, native_enum=False), nullable=False
    )

    product: Mapped[Product] = relationship(back_populates="allergens")
    allergen: Mapped[Allergen] = relationship()


class ProductNutrition(Base):
    __tablename__ = "product_nutrition"

    product_ean: Mapped[str] = mapped_column(
        ForeignKey("products.ean", ondelete="CASCADE"), primary_key=True
    )
    nutrient_code: Mapped[str] = mapped_column(
        ForeignKey("nutrients.code", ondelete="RESTRICT"), primary_key=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)

    product: Mapped[Product] = relationship(back_populates="nutrition")
    nutrient: Mapped[Nutrient] = relationship()


# ============================================================
# Ingredients domain
# ============================================================

class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    measurement_type: Mapped[MeasurementType] = mapped_column(
        SQLEnum(MeasurementType, native_enum=False), nullable=False
    )

    products: Mapped[list["IngredientProduct"]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )


class IngredientProduct(Base):
    __tablename__ = "ingredient_products"

    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True
    )
    product_ean: Mapped[str] = mapped_column(
        ForeignKey("products.ean", ondelete="RESTRICT"), primary_key=True
    )

    ingredient: Mapped[Ingredient] = relationship(back_populates="products")
    product: Mapped[Product] = relationship()


# ============================================================
# Dishes domain
# ============================================================

class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    portions: Mapped[int] = mapped_column(nullable=False)
    time_minutes: Mapped[int | None] = mapped_column()
    difficulty: Mapped[str | None] = mapped_column(String(20))
    spice_level: Mapped[str | None] = mapped_column(String(20))

    # Nutritional totals per portion (snapshot — see design notes)
    kcal: Mapped[float | None] = mapped_column(Float)
    protein: Mapped[float | None] = mapped_column(Float)
    carbs: Mapped[float | None] = mapped_column(Float)
    fat: Mapped[float | None] = mapped_column(Float)
    fiber: Mapped[float | None] = mapped_column(Float)
    salt: Mapped[float | None] = mapped_column(Float)
    sugar: Mapped[float | None] = mapped_column(Float)

    ingredients: Mapped[list["DishIngredient"]] = relationship(
        back_populates="dish", cascade="all, delete-orphan"
    )
    tools: Mapped[list["DishTool"]] = relationship(
        back_populates="dish", cascade="all, delete-orphan"
    )
    diets: Mapped[list["DishDiet"]] = relationship(
        back_populates="dish", cascade="all, delete-orphan"
    )
    regions: Mapped[list["DishRegion"]] = relationship(
        back_populates="dish", cascade="all, delete-orphan"
    )


class DishIngredient(Base):
    __tablename__ = "dish_ingredients"

    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"), primary_key=True
    )
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

    dish: Mapped[Dish] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()


class DishTool(Base):
    __tablename__ = "dish_tools"

    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True
    )
    tool_id: Mapped[int] = mapped_column(
        ForeignKey("tools.id", ondelete="RESTRICT"), primary_key=True
    )

    dish: Mapped[Dish] = relationship(back_populates="tools")
    tool: Mapped[Tool] = relationship()


class DishDiet(Base):
    __tablename__ = "dish_diets"

    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True
    )
    diet_id: Mapped[int] = mapped_column(
        ForeignKey("diets.id", ondelete="RESTRICT"), primary_key=True
    )

    dish: Mapped[Dish] = relationship(back_populates="diets")
    diet: Mapped[Diet] = relationship()


class DishRegion(Base):
    __tablename__ = "dish_regions"

    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True
    )
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="RESTRICT"), primary_key=True
    )

    dish: Mapped[Dish] = relationship(back_populates="regions")
    region: Mapped[Region] = relationship()