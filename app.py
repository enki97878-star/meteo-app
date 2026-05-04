import sqlite3
from flask import Flask, render_template
import requests
import pandas as pd

app = Flask(__name__)

URL = "https://danepubliczne.imgw.pl/api/data/synop/id/12200"


# 🔹 zapis do bazy
def zapisz_do_bazy(wiersz):
    conn = sqlite3.connect("dane.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS pomiary (
            czas TEXT PRIMARY KEY,
            data TEXT,
            godzina INTEGER,
            stacja TEXT,
            temperatura REAL,
            wiatr REAL
        )
    """)

    try:
        c.execute("""
            INSERT INTO pomiary (czas, data, godzina, stacja, temperatura, wiatr)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            wiersz["czas"],
            wiersz["data"],
            wiersz["godzina"],
            wiersz["stacja"],
            wiersz["temperatura"],
            wiersz["wiatr"]
        ))
        conn.commit()
        print("Dodano:", wiersz)

    except:
        print("Pomiar już istnieje")

    conn.close()


# 🔹 pobierz dane JEDNORAZOWO
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


# 🔹 strona główna
@app.route("/")
def index():
    # 👉 przy każdym wejściu zapisuje nowy pomiar
    pobierz_dane()

    conn = sqlite3.connect("dane.db")

    df = pd.read_sql_query("""
        SELECT * FROM pomiary
        ORDER BY czas DESC
        LIMIT 50
    """, conn)

    conn.close()

    return render_template("index.html", dane=df)


if __name__ == "__main__":
    app.run(debug=True)
