import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.name_and_measurements import NameAndMeasurements
from src.meal import Meal

load_dotenv()

class Translator:
    def translate_meal(self, meal):
        raise NotImplementedError
    
class FakeTranslator(Translator):
    def translate_meal(self, meal):
        new_ingredients = [NameAndMeasurements("NO-" + ingredient.name, ingredient.measurement) for ingredient in meal.ingredients]
        
        return Meal(meal.id, "NO-" + meal.mealName, new_ingredients, meal.country, meal.category)

class GeminiTranslator(Translator):
    def __init__(self, model="gemini-2.5-flash"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY mangler. Sjekk at .env-filen finnes og er riktig.")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def translate_meal(self, meal):
        prompt = self._build_prompt(meal)

        response = self.client.models.generate_content(
            model=self.model, 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
            )

        try:
            data = json.loads(response.text)
            # data er nå en liste: [{"id": 1, "navn": "...", "maal": "..."}, ...]
        except json.JSONDecodeError:
            print("Klarte ikke å parse JSON. RÅ svar var:")
            print(response.text)
            raise
        
        if len(data["ingredienser"]) != len(meal.ingredients):
            print(f"Advarsel: sendte {len(meal.ingredients)}, fikk {len(data['ingredienser'])} tilbake")

        new_name = data["rettnavn"]
        new_ingredients = [
            NameAndMeasurements(item["navn"], item["maal"])
            for item in data["ingredienser"]
        ]

        return Meal(meal.id, new_name, new_ingredients, meal.country, meal.category)
    
    def _build_prompt(self, meal):
        lines = []
        for number, ingredient in enumerate(meal.ingredients, start=1):
            lines.append(f"{number}. {ingredient.name} - {ingredient.measurement}")
        ingredient_block = "\n".join(lines)

        prompt = f"""
Du oversetter ingredienser fra en matoppskrift til norsk.

Konteksten er retten "{meal.mealName}" - en {meal.category}-rett fra {meal.country}.
Bruk denne konteksten til å velge riktig oversettelse når et ord kan bety flere ting.

For hver ingrediens nedenfor:

- Oversett navnet til korrekt norsk matterm. Vær oppmerksom på falske venner:
  "baking soda" er natron (ikke bakepulver), "heavy cream" er kremfløte,
  "caster sugar" er strøsukker, "icing sugar" er melis. Velg matbetydningen
  av et ord (frukten "orange" er appelsin, ikke fargen oransje).

- Behold måleenheter som allerede finnes på norsk, men oversett ordet:
  "tablespoon" → "spiseskje", "teaspoon" → "teskje", "pinch" → "en klype",
  "handful" → "en håndfull", "clove" → "fedd". Ikke regn disse om til dl eller gram.

- Konverter KUN måleenheter som ikke finnes på norsk:
  "cup" og "cups" → gram eller dl, avhengig av ingrediensen (1 cup mel ≈ 120 g,
  1 cup sukker ≈ 200 g, 1 cup væske ≈ 2,4 dl — vekten avhenger av ingrediensen,
  så bruk skjønn). "lb"/"pound" og "oz"/"ounce" → gram.

- Hvis målet er et uttrykk som ikke kan tallfestes ("to taste", "to serve",
  "for brushing", "sprinkling"), oversett uttrykket naturlig i stedet.

- Oversett også selve rettnavnet til norsk. Hvis navnet er et egennavn eller et
  begrep uten norsk ekvivalent (for eksempel "Adana kebab"), la det stå.

Ingredienser:
{ingredient_block}

Svar med KUN gyldig JSON, uten forklaring og uten markdown. Format:
{{"rettnavn": "...", "ingredienser": [{{"id": 1, "navn": "...", "maal": "..."}}]}}
Behold samme id-nummer som i listen over.
        """

        return prompt