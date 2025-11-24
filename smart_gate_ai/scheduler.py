import schedule
import time
from datetime import datetime
from smart_gate_ai.modules.report_module import buat_laporan_pdf
from dotenv import load_dotenv
import os

# ===== Load admin password dari .env =====
load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "superadmin123")

# ===== LOGIN ADMIN =====
pwd = input("Masukkan password admin: ")
if pwd != ADMIN_PASSWORD:
    print("❌ Password salah! Program dihentikan.")
    exit()
print("✅ Password benar, scheduler dijalankan...")

# ===== JOB HARUS DIJALANKAN =====
def job():
    print(f"⏰ Generate laporan PDF: {datetime.now()}")
    buat_laporan_pdf()

# Set jadwal tiap hari jam 23:59
schedule.every().day.at("23:59").do(job)

print("🟢 Scheduler aktif, menunggu jam 23:59...")

# Loop utama scheduler
while True:
    schedule.run_pending()
    time.sleep(30)  # cek setiap 30 detik
