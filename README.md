# MIDDA - FIRST ITERATION

Henter middagsretter fra TheMealDB, rydder opp i dataene, og oversetter
dem til norsk med kontekstbevisst oversettelse (Gemini).

## Oppsett

1. Installer avhengigheter:
   pip install -r requirements.txt

2. Lag en fil `.env` i prosjektroten med din Gemini-nøkkel:
   GEMINI_API_KEY=din-nøkkel-her

   (Nøkkel fås gratis på https://aistudio.google.com)

## Bruk

from src.get_recipes import get_translated_recipes
from src.translations import GeminiTranslator, FakeTranslator

# Ekte oversetting (bruker API-kvote):
retter = get_translated_recipes(3, GeminiTranslator())

# Utvikling uten å bruke kvote:
retter = get_translated_recipes(3, FakeTranslator())

Funksjonen returnerer en liste med `Meal`-objekter. Hver `Meal` har
`.id`, `.mealName`, `.ingredients` (liste av `NameAndMeasurements` med
`.name` og `.measurement`), `.country` og `.category`.

## Merk

Gemini sin gratis-tier har en dagsgrense, så `GeminiTranslator` bør
brukes sparsomt under utvikling — bruk `FakeTranslator` ellers.
