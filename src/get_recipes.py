import requests
from src.meal import Meal

def get_translated_recipes(amount, translator):
    url = "https://www.themealdb.com/api/json/v1/1/search.php"
    response = requests.get(url, params={"f": "a"})
    theMealDB_meals = response.json()["meals"]

    translated = []

    for m in theMealDB_meals[:amount]:
        meal = Meal.from_api(m)
        try:
            translated.append(translator.translate_meal(meal))
        except Exception as e:
            print(f"FEIL ved oversetting av '{meal.mealName}': {e}")

    return translated