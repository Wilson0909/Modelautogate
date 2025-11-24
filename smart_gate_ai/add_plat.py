import sqlite3
import os

# Path ke database
BASE_DIR = os.path.dirname(os.path.abspath(
    '_/Users/wilsonzeng/Documents/smart_gate_ai/smart_gate_ai/smart_gate_ai/db/smartgate.db'))
DB_PATH = os.path.join(BASE_DIR, "smart_gate_ai", "db", "smartgate.db")

print("DB PATH:", DB_PATH)


def get_conn():
    return sqlite3.connect(DB_PATH)

def add_plat(nama, plat):
    
    conn = get_conn()
    c = conn.cursor()

    # cek apakah plat sudah ada
    c.execute("SELECT * FROM plat_terdaftar WHERE plat=?", (plat,))
    exist = c.fetchone()

    if exist:
        print(f"[⚠] Plat '{plat}' sudah terdaftar sebelumnya!")
        conn.close()
        return

    c.execute("""
        INSERT INTO plat_terdaftar (nama, plat)
        VALUES (?, ?)
    """, (nama, plat))

    conn.commit()
    conn.close()
    print(f"[✅] Plat '{plat}' berhasil ditambahkan untuk '{nama}'")


if __name__ == "__main__":
    print("[Tambah Plat ke Database]")

    nama = input("Masukkan nama pemilik: ")
    plat = input("Masukkan nomor plat: ").upper().replace(" ", "")

    add_plat(nama, plat)
