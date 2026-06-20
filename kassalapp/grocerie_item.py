class GrocerieItem:
    def __init__(self, name: str, price: float, weight: str, store: str, image: str):
        self.name = name
        self.price = price
        self.weight = weight
        self.store = store
        self.image = image

    @classmethod
    def from_api(cls, item: dict) -> "GrocerieItem": #Brukes som en classmethod for å kunne bruke cls i stedet for GrocerieItem
        w = item.get("weight")
        wu = item.get("weight_unit") or ""
        weight = f"{w} {wu}".strip() if w else None

        return cls(
            name=item["name"],
            price=item["current_price"],
            weight=weight,
            store=item["store"]["name"],
            image=item.get("image"),
        )

    @staticmethod
    def parse_list(items: list[dict]) -> list["GrocerieItem"]:
        return [GrocerieItem.from_api(item) for item in items]

    def __repr__(self):
        return (
            f"GrocerieItem(name={self.name!r}, price={self.price}, "
            f"weight={self.weight!r}, store={self.store!r})"
        )
