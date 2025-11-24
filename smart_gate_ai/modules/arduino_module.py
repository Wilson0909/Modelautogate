import serial
import time

# Konfigurasi port dan baudrate
SERIAL_PORT = "COM13"
BAUD_RATE = 9600

try:
    arduino = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
    time.sleep(2)  # Tunggu koneksi stabil
    print(f"[INFO] Terhubung ke Arduino di {SERIAL_PORT}")
except serial.SerialException as e:
    print(f"[ERROR] Tidak bisa terhubung ke Arduino: {e}")
    arduino = None


def buka_plang():
    """Mengirim sinyal ke Arduino untuk membuka plang."""
    if arduino and arduino.is_open:
        arduino.write(b'1')  # Kirim sinyal '1' ke Arduino
        print("[INFO] Sinyal buka plang dikirim ke Arduino 🚧")
    else:
        print("[WARNING] Arduino tidak terhubung.")


def notif_tolak():
    """Mengirim sinyal ke Arduino untuk menolak (tidak buka plang)."""
    if arduino and arduino.is_open:
        arduino.write(b'0')  # Kirim sinyal '0' ke Arduino
        print("[INFO] Sinyal tolak akses dikirim ke Arduino ❌")
    else:
        print("[WARNING] Arduino tidak terhubung.")
