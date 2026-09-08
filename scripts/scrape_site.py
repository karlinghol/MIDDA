import requests
import sys
from recipe_scrapers import scrape_html


url = sys.argv[1]


def scrape_site(url):
    html = requests.get(url, headers={"User-Agent": "Midda/0.1"}).text

    scraper = scrape_html(html, org_url=url)
    print(scraper.title())
    print(scraper.total_time())        # minutter, som int
    print(scraper.yields())            # f.eks. "4 servings"
    print(scraper.ingredients())       # liste med strenger
    print(scraper.instructions_list()) # liste med steg 

if __name__ == "__main__":
    scrape_site(url)