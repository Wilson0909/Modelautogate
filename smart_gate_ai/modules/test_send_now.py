# test_send_now.py
from smart_gate_ai.modules.report_module import buat_laporan_pdf
from datetime import datetime

if __name__ == "__main__":
    print("=== Generate Laporan Smart Gate AI ===")
    tgl = input("Masukkan tanggal laporan (YYYY-MM-DD) atau enter untuk hari ini: ").strip()

    if tgl == "":
        tgl = datetime.now().strftime("%Y-%m-%d")

    buat_laporan_pdf(tgl)
        