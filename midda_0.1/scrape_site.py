import requests
from recipe_scrapers import scrape_html

url = "https://www.matprat.no/oppskrifter/rask/gnocchi-cacio-e-pepe/"
html = requests.get(url, headers={"User-Agent": "Midda/0.1"}).text

scraper = scrape_html(html, org_url=url)

print(scraper.title())
print(scraper.total_time())        # minutter, som int
print(scraper.yields())            # f.eks. "4 servings"
print(scraper.ingredients())       # liste med strenger
print(scraper.instructions_list()) # liste med steg
print(scraper.nutrients())         # dict


def scrape_site(urL):
    html = requests.get(url, headers={"User-Agent": "Midda/0.1"}).text

    scraper = scrape_html(html, org_url=url)

    