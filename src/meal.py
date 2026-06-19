from src.name_and_measurements import NameAndMeasurements

class Meal:
    def __init__(self, meal_id, name, ingredients, country, category):
        self.id = meal_id
        self.mealName = name
        self.ingredients = ingredients
        self.country = country
        self.category = category

    @classmethod
    def from_api(cls, meal_dict):
        meal_id = meal_dict["idMeal"]
        name = cls._clean(meal_dict["strMeal"])
        ingredients = cls._make_ingredient_list(meal_dict)
        country = cls._clean(meal_dict.get("strCountry"))
        category = cls._clean(meal_dict.get("strCategory"))
        return cls(meal_id, name, ingredients, country, category)
    
    @staticmethod
    def _clean(text):
        return " ".join((text or "").split())
    
    @staticmethod
    def _make_ingredient_list(meal_dict):
        listIngredients = []
        strIngredient = "strIngredient"
        strMeasure = "strMeasure"

        for i in range(1, 21):
            if Meal._clean(meal_dict[strIngredient + str(i)]) == "":
                continue

            listIngredients.append(
                NameAndMeasurements(
                    Meal._clean(meal_dict[strIngredient + str(i)]), 
                    Meal._clean(meal_dict[strMeasure + str(i)])
                    )
                )

        return listIngredients
    
    def __repr__(self):
        return f'Meal("{self.id}", "{self.mealName}", {self.ingredients}, "{self.country}", "{self.category}")'