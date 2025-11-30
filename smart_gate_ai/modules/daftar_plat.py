import sqlite3

DB_PATH = "smartgate.db"

def daftar_plat(nama, plat):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO plat_terdaftar (nama, plat) VALUES (?, ?)", (nama, plat))
        conn.commit()
        print(f"✅ Plat '{plat}' berhasil didaftarkan untuk {nama}")
    except sqlite3.IntegrityError:
        print(f"⚠️ Plat '{plat}' sudah ada di database")
    conn.close()

# --- Contoh penggunaan ---
daftar_plat("Arman", "BP2053DY")
daftar_plat("Budi",  "B1001ZZZ")
