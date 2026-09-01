"""
Test-script for å inspisere rå JSON-respons fra Kassal.app.

Formål:
- Se nøyaktig hvilke felter API-et returnerer per produkt
- Kartlegge om kategori, merkevare, EAN og lignende er utfylt konsistent
- Sammenligne støynivå mellom ulike søkeord og parametere
- Lagre respons til fil så vi kan analysere den sammen etterpå

Kjøres fra prosjektroten der .env ligger:
    python test_kassal_raw.py
"""

from dotenv import load_dotenv
import requests
import os
import json
from pathlib import Path

load_dotenv()

API_TOKEN = os.getenv("KASSAL_API_TOKEN")
URL = "https://kassal.app/api/v1/products"

# Søkeord vi vil se på. Melk er den klassiske støy-caset ditt.
# De andre er valgt for å teste ulike scenarier:
# - "kylling": bredt, mange varianter
# - "hvetemel": sammensatt ord, sjelden feilmatchet
# - "smør": kort ord, kolliderer med "smørbrød", "smørepålegg" osv.
# - "egg": veldig kort, mange sammensetninger
SEARCH_TERMS = ["melk", "kylling", "hvetemel", "smør", "egg"]

# Vi tester også med og uten unique-parameteren for å se hvor mye støy den fjerner.
PARAM_VARIANTS = [
    {"sort": "price_desc"},
    {"sort": "price_desc", "unique": "true"},
]

OUTPUT_DIR = Path("kassal_raw_dumps")
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch(search_term: str, extra_params: dict) -> dict | None:
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    params = {"search": search_term, **extra_params}

    response = requests.get(URL, headers=headers, params=params)

    if response.status_code != 200:
        print(f"  Feil ({response.status_code}): {response.text[:200]}")
        return None

    return response.json()


def summarize(search_term: str, params: dict, payload: dict) -> None:
    """Print en kompakt oversikt så vi ser strukturen uten å drukne i JSON."""
    data = payload.get("data", []) or []
    variant_label = "unique" if params.get("unique") == "true" else "default"

    print(f"\n=== '{search_term}' [{variant_label}] — {len(data)} treff ===")

    if not data:
        return

    # Vis hvilke nøkler første produkt har — kartlegg felter.
    first = data[0]
    print(f"Felter på første produkt: {sorted(first.keys())}")

    # Hvor mange har kategori, merkevare, EAN utfylt?
    def count_filled(key: str) -> int:
        return sum(1 for p in data if p.get(key))

    for key in ["category", "brand", "ean", "vendor", "store", "image"]:
        if key in first:
            print(f"  {key} utfylt: {count_filled(key)}/{len(data)}")

    # Vis de første 15 produktnavnene så vi ser støynivået med egne øyne.
    print("Første 15 navn:")
    for p in data[:15]:
        name = p.get("name", "(uten navn)")
        # Hvis kategori er en dict/liste, vis siste ledd; ellers rå verdi.
        cat = p.get("category")
        if isinstance(cat, list) and cat:
            cat_str = " > ".join(str(c.get("name", c)) if isinstance(c, dict) else str(c) for c in cat)
        elif isinstance(cat, dict):
            cat_str = cat.get("name", "")
        else:
            cat_str = str(cat) if cat else ""
        print(f"  - {name}  [{cat_str}]")


def main() -> None:
    if not API_TOKEN:
        print("KASSAL_API_TOKEN er ikke satt i .env")
        return

    for term in SEARCH_TERMS:
        for params in PARAM_VARIANTS:
            payload = fetch(term, params)
            if payload is None:
                continue

            summarize(term, params, payload)

            # Lagre full respons til fil for videre analyse.
            variant_label = "unique" if params.get("unique") == "true" else "default"
            out_path = OUTPUT_DIR / f"{term}_{variant_label}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"  → lagret full respons til {out_path}")


if __name__ == "__main__":
    main()