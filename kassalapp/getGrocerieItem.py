from dotenv import load_dotenv
import requests
import os

try:
    from kassalapp.grocerie_item import GrocerieItem
except ModuleNotFoundError:
    from grocerie_item import GrocerieItem

load_dotenv()  # Last inn miljøvariabler fra .env-filen

API_TOKEN = os.getenv("KASSAL_API_TOKEN")  # Hent API-token fra miljøvariabler

url = "https://kassal.app/api/v1/products"

def get_grocerie_item(search_term: str, sort: str = "price_desc") -> list[dict] | None:
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    params = {
        "search": search_term, "sort": sort
        }
    
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Feil: {response.status_code}")
        print(response.text)
        return None
    

def main():
    search_term = "melk"
    items = get_grocerie_item(search_term)
    if items:
        for g in GrocerieItem.parse_list(items):
            print(g)

if __name__ == "__main__":
    main()