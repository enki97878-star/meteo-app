from flask import Flask, render_template
import requests
import pandas as pd
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)

URL = "https://danepubliczne.imgw.pl/api/data/synop/id/12200"

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


# tworzenie tabeli
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pomiary (
            czas TEXT PRIMARY KEY,
            data TEXT,
            godzina INTEGER,
            stacja TEXT,
            temperatura REAL,
            wiatr REAL
        )
    """))
    conn.commit()


def zapisz_do_bazy(wiersz):

    with engine.connect() as conn:

        istnieje = conn.execute(
            text("SELECT czas FROM pomiary WHERE czas=:czas"),
            {"czas": wiersz["czas"]}
        ).fetchone()

        if not istnieje:

            conn.execute(text("""
                INSERT INTO pomiary
                (czas, data, godzina, stacja, temperatura, wiatr)

                VALUES
                (:czas, :data, :godzina, :stacja, :temperatura, :wiatr)
            """), wiersz)

            conn.commit()

            print("Dodano:", wiersz)

        else:
            print("Pomiar już istnieje")


def pobierz_dane():

    try:
        response = requests.get(URL)
        data = response.json()

        wiersz = {
            "data": data["data_pomiaru"],
            "godzina": int(data["godzina_pomiaru"]),
            "czas": f'{data["data_pomiaru"]} {data["godzina_pomiaru"]}:00',
            "stacja": data["stacja"],
            "temperatura": float(data["temperatura"]),
            "wiatr": float(data["predkosc_wiatru"])
        }

        zapisz_do_bazy(wiersz)

    except Exception as e:
        print("Błąd:", e)


@app.route("/")
def index():

    pobierz_dane()

    query = """
        SELECT *
        FROM pomiary
        ORDER BY czas DESC
        LIMIT 50
    """

    df = pd.read_sql(query, engine)

    return render_template("index.html", dane=df)


if __name__ == "__main__":
    app.run(debug=True)