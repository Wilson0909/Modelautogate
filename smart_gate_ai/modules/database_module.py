import sqlite3
import os
from datetime import datetime
from smart_gate_ai.firebase_init import db

# Path ke SQLite
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "smartgate.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kendaraan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plat TEXT,
                    status TEXT,
                    waktu_masuk TEXT,
                    waktu_keluar TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS plat_terdaftar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT,
                    plat TEXT
                )''')
    conn.commit()
    conn.close()

def tambah_plat_manual(nama, plat):
    conn = get_connection()
    c = conn.cursor()

    # cek apakah plat sudah ada
    c.execute("SELECT * FROM plat_terdaftar WHERE plat=?", (plat,))
    exist = c.fetchone()

    if exist:
        print(f"[⚠] Plat '{plat}' sudah terdaftar!")
        conn.close()
        return

    c.execute("INSERT INTO plat_terdaftar (nama, plat) VALUES (?, ?)", (nama, plat))
    
    # ambil ID SQLite terakhir
    row_id = c.lastrowid

    conn.commit()
    conn.close()

    print(f"[✅] Plat '{plat}' milik '{nama}' berhasil ditambahkan! (ID={row_id})")

    # SIMPAN KE FIREBASE DENGAN ID YANG SAMA
    db.collection("plat_terdaftar").document(str(row_id)).set({
        "id": row_id,
        "nama": nama,
        "plat": plat
    })
    print("🔥 Firebase updated: Data plat_terdaftar ditambahkan!")

def cek_plat(plat):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM plat_terdaftar WHERE plat=?", (plat,))
    data = c.fetchone()
    conn.close()
    return data

# 🔥 kirim ke Firebase (pakai id SQLite)
def firebase_log(row_id, plat, status, waktu_masuk=None, waktu_keluar=None):
    data = {
        "id": row_id,
        "plat": plat,
        "status": status,
        "waktu_masuk": waktu_masuk,
        "waktu_keluar": waktu_keluar
    }
    db.collection("smartgate_logs").document(str(row_id)).set(data)
    print("🔥 Firebase updated:", data)

def catat_masuk(plat, status):
    conn = get_connection()
    c = conn.cursor()
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Simpan lokal SQLite
    c.execute("INSERT INTO kendaraan (plat, status, waktu_masuk) VALUES (?, ?, ?)", 
              (plat, status, waktu))

    row_id = c.lastrowid  # ambil ID auto increment
    conn.commit()
    conn.close()

    # Simpan Firebase pakai id SQLite
    firebase_log(row_id, plat, "masuk", waktu_masuk=waktu)

def catat_keluar(plat):
    conn = get_connection()
    c = conn.cursor()
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("UPDATE kendaraan SET waktu_keluar=? WHERE plat=? AND waktu_keluar IS NULL",
              (waktu, plat))

    # Ambil kembali row ID kendaraan yg keluar
    c.execute("SELECT id FROM kendaraan WHERE plat=? ORDER BY id DESC LIMIT 1", (plat,))
    row_id = c.fetchone()[0]

    conn.commit()
    conn.close()

    # Simpan Firebase
    firebase_log(row_id, plat, "keluar", waktu_keluar=waktu)

if __name__ == "__main__":
    init_db()
    print("✅ Database berhasil diinisialisasi di:", DB_PATH)

    print("\n[Tambah Plat Manual]")
    nama = input("Masukkan nama pemilik: ")
    plat = input("Masukkan nomor plat: ").upper().replace(" ", "")

    tambah_plat_manual(nama, plat)
