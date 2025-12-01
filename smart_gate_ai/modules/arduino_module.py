import serial
import time

SERIAL_PORT = "COM9"
BAUD_RATE = 9600

try:
    arduino = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"[INFO] Terhubung ke Arduino di {SERIAL_PORT}")
except serial.SerialException as e:
    print(f"[ERROR] Tidak bisa terhubung ke Arduino: {e}")
    arduino = None


# ========== GENERIC SENDER ==========
def send(cmd: str):
    if arduino and arduino.is_open:
        arduino.write((cmd + "\n").encode())
        print(f"[Arduino] >> {cmd}")
    else:
        print("[WARNING] Arduino tidak terhubung.")


# ==========================
# MODE MASUK (M)
# ==========================

def buka_plang():
    """Buka plang GATE MASUK"""
    send("M:OPEN")


def notif_tolak():
    """Tolak akses GATE MASUK"""
    send("M:REJECT")


def kirim_plat(plat: str):
    """Kirim plat ke LCD GATE MASUK"""
    send(f"M:PLAT:{plat}")


# ==========================
# MODE KELUAR (K)
# ==========================

def buka_plang_keluar():
    """Buka plang GATE KELUAR"""
    send("K:OPEN")


def notif_tolak_keluar():
    """Tolak akses GATE KELUAR"""
    send("K:REJECT")


def kirim_plat_keluar(plat: str):
    """Kirim plat ke LCD GATE KELUAR"""
    send(f"K:PLAT:{plat}")
