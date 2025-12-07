import cv2
import threading
import urllib.request
import numpy as np
import time
import re

from smart_gate_ai.modules.ocr_module import recognize_plate
from smart_gate_ai.modules.arduino_module import (
    buka_plang_keluar,
    notif_tolak_keluar,
    kirim_plat_keluar,
    tutup_plang_keluar  # ⬅️ FIX: Import fungsi tutup palang
)
from smart_gate_ai.modules.database_module import cek_plat, catat_keluar


# ==================================================
# CONFIG
# ==================================================
ESP32_IP = "10.171.3.4"
STREAM_URL = f"http://{ESP32_IP}/capture"

CONFIDENCE_THRESHOLD = 0.60
OCR_INTERVAL = 0.8
CAMERA_DELAY = 0.15
PLATE_COOLDOWN = 5
PALANG_OPEN_TIME = 5


# ==================================================
# GLOBAL STATE
# ==================================================
frame_lock = threading.Lock()
latest_frame = None
running = True

last_ocr_time = 0
processed_plates = set()

palang_terbuka = False
last_open_time = 0


# ==================================================
# CAMERA THREAD
# ==================================================
def camera_thread():
    global latest_frame, running
    print("[THREAD] ESP32-CAM KELUAR started")

    while running:
        try:
            resp = urllib.request.urlopen(STREAM_URL, timeout=3)
            img_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is not None:
                with frame_lock:
                    latest_frame = frame

            time.sleep(CAMERA_DELAY)

        except Exception as e:
            print("❌ Kamera KELUAR error:", e)
            time.sleep(0.5)


threading.Thread(target=camera_thread, daemon=True).start()

print("\n[INFO] SMART GATE AI — MODE KELUAR")
print("Tekan Q untuk berhenti.\n")


# ==================================================
# MAIN LOOP
# ==================================================
while True:
    with frame_lock:
        if latest_frame is None:
            continue
        frame = latest_frame.copy()

    now = time.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    cv2.putText(frame, timestamp, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    status_text = "Menunggu kendaraan keluar..."
    color = (255, 255, 255)
    bbox = None

    # ==================================================
    # AUTO CLOSE PALANG (tanpa LED merah)
    # ==================================================
    if palang_terbuka and now - last_open_time >= PALANG_OPEN_TIME:
        tutup_plang_keluar()  # ⬅️ FIX BENAR: tidak kirim LED merah
        palang_terbuka = False


    # ==================================================
    # OCR EXECUTION TIMER
    # ==================================================
    if now - last_ocr_time >= OCR_INTERVAL:
        last_ocr_time = now

        try:
            plate, conf, bbox = recognize_plate(frame)
        except Exception as e:
            print("[OCR ERROR]", e)
            plate, conf, bbox = None, 0, None

        if plate:
            plate_clean = re.sub(r"\s+", "", plate.upper())
            print(f"[{timestamp}] OCR KELUAR: '{plate_clean}' | Conf: {conf:.2f}")

            # Sudah diproses sebelumnya → tidak buka lagi
            if plate_clean in processed_plates:
                status_text = f"{plate_clean} — Sudah Keluar"
                color = (255, 255, 0)

            else:
                # Validasi format nomor plat
                valid = re.match(r"^[A-Z]{1,2}\d{1,4}[A-Z]{2,3}$", plate_clean)

                if not valid:
                    status_text = f"{plate_clean} — Format Tidak Valid"
                    color = (0, 0, 255)

                elif conf < CONFIDENCE_THRESHOLD:
                    status_text = f"{plate_clean} — Confidence Rendah ({conf:.2f})"
                    color = (0, 0, 255)

                else:
                    kirim_plat_keluar(plate_clean)
                    data = cek_plat(plate_clean)

                    if data:
                        if not palang_terbuka:
                            buka_plang_keluar()
                            palang_terbuka = True
                            last_open_time = now

                            catat_keluar(plate_clean, "Keluar")
                            processed_plates.add(plate_clean)

                            status_text = f"{plate_clean} — Diizinkan Keluar"
                            color = (0, 255, 0)
                        else:
                            status_text = "Palang masih terbuka..."

                    else:
                        status_text = f"{plate_clean} — Tidak Terdaftar"
                        color = (0, 255, 255)
                        notif_tolak_keluar()  # LED Merah ONLY untuk yang ditolak

        else:
            status_text = "Plat tidak terdeteksi"


    # ==================================================
    # UI DISPLAY
    # ==================================================
    if bbox:
        x, y, w, h = bbox
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, status_text, (x, max(20, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    else:
        cv2.putText(frame, status_text, (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Smart Gate AI — KELUAR (ESP32 CAM)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# ==================================================
# SHUTDOWN
# ==================================================
running = False
cv2.destroyAllWindows()
print("\n[INFO] SMART GATE AI STOPPED\n")