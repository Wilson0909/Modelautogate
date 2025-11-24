# test_send_now.py
from smart_gate_ai.modules.report_module import buat_laporan_pdf

if __name__ == "__main__":
    buat_laporan_pdf()
    print("Selesai. Cek folder, scheduler_log.txt, dan inbox email.")
