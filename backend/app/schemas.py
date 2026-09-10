from __future__ import annotations

from pydantic import BaseModel, HttpUrl

from backend.app.models import Dish, DishIngredient


class ImportRequest(BaseModel):
    url: HttpUrl


class DishIngredientOut(BaseModel):
    amount: float
    unit: str
    ingredient: str
    note: str | None

    @classmethod
    def from_dish_ingredient(cls, dish_ingredient: DishIngredient) -> DishIngredientOut:
        return cls(
            amount=dish_ingredient.amount,
            unit=dish_ingredient.unit.value,
            ingredient=dish_ingredient.ingredient.name,
            note=dish_ingredient.note,
        )


class DishOut(BaseModel):
    id: int
    name: str
    total_time: int
    yields: int
    instructions_list: list[str]
    ingredients: list[DishIngredientOut]

    @classmethod
    def from_dish(cls, dish: Dish) -> DishOut:
        return cls(
            id=dish.id,
            name=dish.name,
            total_time=dish.total_time,
            yields=dish.yields,
            instructions_list=dish.instructions_list,
            ingredients=[
                DishIngredientOut.from_dish_ingredient(di) for di in dish.ingredients
            ],
        )
