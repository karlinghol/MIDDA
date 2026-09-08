import re

import requests
from recipe_scrapers import scrape_html
from recipe_scrapers._exceptions import NoSchemaFoundInWildMode, WebsiteNotImplementedError

from app.database import SessionLocal
from app.models import Dish, DishIngredient, Ingredient, Unit

UNIT_WORDS = {
    "g": Unit.G,
    "gram": Unit.G,
    "kg": Unit.KG,
    "ml": Unit.ML,
    "dl": Unit.DL,
    "l": Unit.L,
    "ts": Unit.TS,
    "teskje": Unit.TS,
    "teskjeer": Unit.TS,
    "ss": Unit.SS,
    "spiseskje": Unit.SS,
    "spiseskjeer": Unit.SS,
    "stk": Unit.STK,
    "klype": Unit.KLYPE,
}

AMOUNT_RE = re.compile(r"^\s*(?P<amount>\d+(?:[.,]\d+)?(?:/\d+)?)\s+(?P<rest>.+)$")


class ScrapeError(Exception):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


def _parse_amount(raw: str) -> float:
    raw = raw.strip()
    if "/" in raw:
        num, denom = raw.split("/")
        return float(num) / float(denom)
    return float(raw.replace(",", "."))


def parse_ingredient_line(line: str) -> tuple[float, Unit, str, str | None]:
    """'75 g pecorino' -> (75.0, Unit.G, 'pecorino', None)
    '1/2 ts natron'   -> (0.5, Unit.TS, 'natron', None)
    '2 fedd hvitløk'  -> (2.0, Unit.STK, 'fedd hvitløk', '2 fedd hvitløk')  (ukjent måleord)
    'olje til steking' -> (1.0, Unit.STK, 'olje til steking', 'olje til steking')  (ingen mengde)
    """
    match = AMOUNT_RE.match(line)
    if not match:
        return 1.0, Unit.STK, line.strip(), line.strip()

    amount = _parse_amount(match.group("amount"))
    rest = match.group("rest").strip()
    first_word, _, remainder = rest.partition(" ")
    unit = UNIT_WORDS.get(first_word.lower())

    if unit is not None and remainder:
        return amount, unit, remainder.strip(), None

    # Måleordet er ikke i Unit-enumen (fedd, boks, stilker, cm, ...), eller det
    # er ingen enhet i teksten i det hele tatt (f.eks. "4 sjampinjonger").
    # Mengden beholdes, STK brukes som enhet, og original tekst legges i note
    # så det er lett å finne igjen og evt. utvide Unit-enumen senere.
    return amount, Unit.STK, rest, line.strip()


def _extract_yields(raw) -> int:
    if raw is None:
        return 1
    match = re.search(r"\d+", str(raw))
    return int(match.group()) if match else 1


def fetch_and_scrape(url: str) -> Dish:
    try:
        html = requests.get(url, headers={"User-Agent": "Midda/0.1"}, timeout=10).text
    except requests.RequestException as exc:
        raise ScrapeError("fetch_failed", str(exc)) from exc

    try:
        scraped_dish = scrape_html(html, org_url=url)
    except (WebsiteNotImplementedError, NoSchemaFoundInWildMode) as exc:
        raise ScrapeError("unsupported_domain", str(exc)) from exc

    dish = Dish(
        name=str(scraped_dish.title()),
        total_time=int(scraped_dish.total_time() or 0),
        yields=_extract_yields(scraped_dish.yields()),
        instructions_list=scraped_dish.instructions_list(),
    )

    db = SessionLocal()
    try:
        ingredients_by_name: dict[str, Ingredient] = {}
        dish_ingredients_by_name: dict[str, DishIngredient] = {}

        for raw_line in scraped_dish.ingredients():
            amount, unit, name, note = parse_ingredient_line(raw_line)

            # Samme ingrediens kan stå på flere linjer i én oppskrift (f.eks.
            # "olje til steking" både i marinaden og til steking). dish_ingredients
            # har en unik-constraint på (dish_id, ingredient_id), så vi slår sammen
            # mengden i stedet for å lage en duplikatrad.
            existing = dish_ingredients_by_name.get(name)
            if existing is not None and existing.unit == unit:
                existing.amount += amount
                continue

            ingredient = ingredients_by_name.get(name)
            if ingredient is None:
                ingredient = db.query(Ingredient).filter(Ingredient.name == name).first()
            if ingredient is None:
                ingredient = Ingredient(name=name)
            ingredients_by_name[name] = ingredient

            dish_ingredient = DishIngredient(ingredient=ingredient, amount=amount, unit=unit, note=note)
            dish.ingredients.append(dish_ingredient)
            dish_ingredients_by_name[name] = dish_ingredient

        db.add(dish)
        db.commit()
        db.refresh(dish)

        # Sesjonen lukkes rett under - hent inn relasjonene mens den fortsatt
        # er åpen, ellers feiler dish.ingredients med DetachedInstanceError
        # hos den som kaller funksjonen.
        for dish_ingredient in dish.ingredients:
            _ = dish_ingredient.ingredient
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return dish
