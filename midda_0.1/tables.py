from sqlalchemy import ForeignKey, String, Integer, Text, 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from sqlalchemy import create_engine

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

class Base(DeclarativeBase):
    pass

class Dish(Base):
    __tablename__ = "dishes"
        #Mapped notasjonen forklarer SQLAlchamy hva slags datatype kolonnen har
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="dish")

class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))


class DishIngredients(Base):
    __tablename__ = "dish_ingredients"

    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"))
    ingreddient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"))
    amount: Mapped[int]
