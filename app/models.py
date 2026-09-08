from __future__ import annotations

import enum
from typing import List
from sqlalchemy import ForeignKey, String, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship

from app.database import Base


class Unit(enum.Enum):
    """Enheter tillatt i oppskrifter"""
    G = "g"
    KG = "kg"
    ML = "ml"
    DL = "dl"
    L = "l"
    TS = "ts"
    SS = "ss"
    STK = "stk"
    KLYPE = "klype"
    FEDD = "fedd"
    BOKS = "boks"
    STILK = "stilk"
    CM = "cm"

class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    total_time: Mapped[int]
    yields: Mapped[int]
    ingredients: Mapped[list[DishIngredient]] = relationship(
        back_populates="dish",
        cascade="all, delete-orphan",
    )
    instructions_list: Mapped[List[str]] = mapped_column(JSON)

class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

    dishes: Mapped[list[DishIngredient]] = relationship(back_populates="ingredient")

class DishIngredient(Base):
    __tablename__ = "dish_ingredients"
    __table_args__ = (
        UniqueConstraint("dish_id", "ingredient_id", name="uq_dish_ingredient"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"), index=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), index=True)

    amount: Mapped[float]
    unit: Mapped[Unit]
    note: Mapped[str | None] = mapped_column(String(120))

    dish: Mapped[Dish] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship(back_populates="dishes")
    
