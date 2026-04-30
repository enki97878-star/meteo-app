import sqlite3
def zapisz_do_bazy(wiersz):
    conn = sqlite3.connect("dane.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS pomiary (
            czas TEXT PRIMARY KEY,
            temperatura REAL,
            wiatr REAL
        )
    """)

    try:
        c.execute("INSERT INTO pomiary VALUES (?, ?, ?)", 
                  (wiersz["czas"], wiersz["temperatura"], wiersz["wiatr"]))
        conn.commit()
        print("Dodano do bazy:", wiersz)
    except:
        print("Pomiar już istnieje")

    conn.close()
from flask import Flask, render_template
import requests
import pandas as pd
import os
import time
import threading

app = Flask(__name__)

URL = "https://danepubliczne.imgw.pl/api/data/synop/id/12200"
PLIK = "dane.csv"

def pobierz_dane():
    while True:
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

            df_nowy = pd.DataFrame([wiersz])

            if os.path.exists(PLIK):
                df_stary = pd.read_csv(PLIK)

                if wiersz["czas"] not in df_stary["czas"].values:
                    df = pd.concat([df_stary, df_nowy], ignore_index=True)
                    df.to_csv(PLIK, index=False)
                    print("Dodano:", wiersz)
            else:
                df_nowy.to_csv(PLIK, index=False)
                print("Utworzono plik")

        except Exception as e:
            print("Błąd:", e)

        time.sleep(3600)  # co 1 godzinę


@app.route("/")
def index():
    if os.path.exists(PLIK):
        df = pd.read_csv(PLIK)
        dane = df.tail(24)  # ostatnie 24 pomiary
    else:
        dane = []

    return render_template("index.html", dane=dane)


# uruchomienie pobierania w tle
threading.Thread(target=pobierz_dane, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)
