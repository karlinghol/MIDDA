from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError

from backend.app.schemas import DishOut, ImportRequest
from backend.app.scraper import ScrapeError, fetch_and_scrape

app = FastAPI(title="Midda")


@app.post("/dishes/import", response_model=DishOut, status_code=201)
def import_dish(payload: ImportRequest) -> DishOut:
    try:
        dish = fetch_and_scrape(str(payload.url))
    except ScrapeError as exc:
        status_code = 422 if exc.kind == "unsupported_domain" else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Retten finnes allerede i databasen"
        ) from exc

    return DishOut.from_dish(dish)
