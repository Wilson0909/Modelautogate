import sqlite3
import os
from datetime import datetime
from smart_gate_ai.firebase_init import db

# ================================
# KONFIGURASI PATH DATABASE SQLITE
# ================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))   # folder smart_gate_ai/
DB_PATH = os.path.join(BASE_DIR, "db", "smartgate.db")

def get_connection():
    return sqlite3.connect(DB_PATH)


# ================================
# INISIALISASI DATABASE
# ================================
def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Tabel log kendaraan
    c.execute('''
        CREATE TABLE IF NOT EXISTS kendaraan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plat TEXT,
            status TEXT,
            waktu_masuk TEXT,
            waktu_keluar TEXT
        )
    ''')

    # Tabel master plat terdaftar
    c.execute('''
        CREATE TABLE IF NOT EXISTS plat_terdaftar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            plat TEXT UNIQUE
        )
    ''')

    conn.commit()
    conn.close()


# ================================
# TAMBAH DATA PLAT KE LOKAL + FIREBASE
# ================================
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

    # simpan lokal SQLite
    c.execute("INSERT INTO plat_terdaftar (nama, plat) VALUES (?, ?)", (nama, plat))
    row_id = c.lastrowid
    conn.commit()
    conn.close()

    print(f"[✅] Plat '{plat}' milik '{nama}' berhasil ditambahkan! (ID={row_id})")

    # simpan Firebase
    db.collection("plat_terdaftar").document(str(row_id)).set({
        "id": row_id,
        "nama": nama,
        "plat": plat
    })
    print("🔥 Firebase updated: plat_terdaftar ditambahkan!")


# ================================
# CEK PLAT TERDAFTAR
# ================================
def cek_plat(plat):
    # Query Firestore berdasarkan field plat
    results = db.collection("plat_terdaftar").where("plat", "==", plat).stream()

    for doc in results:
        data = doc.to_dict()
        return {
            "id": data.get("id"),
            "nama": data.get("nama"),
            "plat": data.get("plat"),
        }

    return None


# ================================
# LOG KE FIREBASE
# ================================
def firebase_log_masuk(row_id, plat, status, waktu_masuk=None):
    data = {
        "id": row_id,
        "plat": plat,
        "status": status,
        "waktu_masuk": waktu_masuk,
    }

    db.collection("logs_masuk").document(str(row_id)).set(data)
    print("🔥 Firebase updated kendaraan masuk:", data)
    
def firebase_log_keluar(row_id, plat, status,waktu_keluar=None):
    data = {
        "id": row_id,
        "plat": plat,
        "status": status,
        "waktu_keluar": waktu_keluar
    }

    db.collection("logs_keluar").document(str(row_id)).set(data)
    print("🔥 Firebase updated kendaraan keluar:", data)


# ================================
# CATAT KENDARAAN MASUK
# ================================
def catat_masuk(plat, status):
    conn = get_connection()
    c = conn.cursor()

    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("INSERT INTO kendaraan (plat, status, waktu_masuk) VALUES (?, ?, ?)",
              (plat, status, waktu))

    row_id = c.lastrowid
    conn.commit()
    conn.close()

    firebase_log_masuk(row_id, plat, "masuk", waktu_masuk=waktu)


# ================================
# CATAT KENDARAAN KELUAR
# ================================
def catat_keluar(plat,status):
    conn = get_connection()
    c = conn.cursor()

    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # update waktu keluar
    c.execute("INSERT INTO kendaraan (plat, status, waktu_keluar) VALUES (?, ?, ?)",
              (plat, status, waktu))

   

    row_id = c.lastrowid
    conn.commit()
    conn.close()

    firebase_log_keluar(row_id, plat, "keluar", waktu_keluar=waktu)


# ================================
# RUN MANUAL SETUP
# ================================
if __name__ == "__main__":
    init_db()
    print("✅ Database berhasil diinisialisasi di:", DB_PATH)

    print("\n[Tambah Plat Manual]")
    nama = input("Nama pemilik: ")
    plat = input("Nomor plat: ").upper().replace(" ", "")

    tambah_plat_manual(nama, plat)