import sqlite3

def create_table() -> None:
    """Oppretter tabellen ingredients hvis den ikke allerede finnes."""
    
    with sqlite3.connect("dish_database.db") as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                measurement TEXT NOT NULL,
                allergies TEXT
            )
        """)
        connection.commit()



def add_ingredient(name: str, measurement: str, allergies: str = None) -> None:
    """Legger til en ny ingrediens i databasen."""
    with sqlite3.connect("dish_database.db") as connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO ingredients (name, measurement, allergies)
            VALUES (?, ?, ?)
        """, (name, measurement, allergies))
        connection.commit()
