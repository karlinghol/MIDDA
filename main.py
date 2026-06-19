from src.get_recipes import get_translated_recipes
from src.translations import FakeTranslator

retter = get_translated_recipes(3, FakeTranslator())

for rett in retter:
    print(rett)