# test_send_now.py
from smart_gate_ai.modules.report_module import buat_laporan_pdf

if __name__ == "__main__":
    print("=== Generate Laporan Smart Gate AI ===")
    tgl = input("Masukkan tanggal laporan (YYYY-MM-DD) atau enter untuk hari ini: ").strip()

    if tgl == "":
        buat_laporan_pdf()  # default hari ini
    else:
        # validasi format
        from datetime import datetime
        try:
            datetime.strptime(tgl, "%Y-%m-%d")
            buat_laporan_pdf(tgl)
        except ValueError:
            print("Format tanggal salah! Gunakan YYYY-MM-DD")
