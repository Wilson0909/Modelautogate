import cv2
import threading
import urllib.request
import numpy as np
import time
import re

from smart_gate_ai.modules.ocr_module import recognize_plate
from smart_gate_ai.modules.arduino_module import (
    buka_plang,
    notif_tolak,
    kirim_plat
)
from smart_gate_ai.modules.database_module import cek_plat, catat_masuk

# ==================================================
# CONFIG
# ==================================================
ESP32_IP = "10.171.3.153"
STREAM_URL = f"http://{ESP32_IP}/capture"

CONFIDENCE_THRESHOLD = 0.60
OCR_INTERVAL = 0.8          # OCR tiap 0.8 detik
CAMERA_DELAY = 0.15         # ≈ 6 FPS (AMAN ESP32)
PLATE_COOLDOWN = 5          # plat sama diabaikan 5 detik
PALANG_OPEN_TIME = 6        # palang terbuka 6 detik

# ==================================================
frame_lock = threading.Lock()
latest_frame = None
running = True

last_ocr_time = 0
plate_last_seen = {}

# STATE PALANG
palang_terbuka = False
last_open_time = 0

# ==================================================
# THREAD CAMERA
# ==================================================
def camera_thread():
    global latest_frame, running
    print("[THREAD] ESP32 Camera started")

    while running:
        try:
            resp = urllib.request.urlopen(STREAM_URL, timeout=3)
            img = np.asarray(bytearray(resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(img, cv2.IMREAD_COLOR)

            if frame is not None:
                with frame_lock:
                    latest_frame = frame

            time.sleep(CAMERA_DELAY)

        except Exception as e:
            print("❌ Kamera error:", e)
            time.sleep(0.5)

threading.Thread(target=camera_thread, daemon=True).start()

print("\n[INFO] SMART GATE AI RUNNING (FULL STABLE MODE)")
print("Tekan Q untuk keluar\n")

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

    status_text = "Menunggu kendaraan..."
    color = (255, 255, 255)
    bbox = None

    # ==================================================
    # AUTO TUTUP PALANG
    # ==================================================
    if palang_terbuka and now - last_open_time >= PALANG_OPEN_TIME:
        notif_tolak()          # ganti ke tutup_plang() jika ada
        palang_terbuka = False

    # ==================================================
    # OCR TIMER
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
            print(f"[{timestamp}] OCR: '{plate_clean}' | Conf: {conf:.2f}")

            # =============================
            # PLATE COOLDOWN
            # =============================
            if plate_clean in plate_last_seen:
                if now - plate_last_seen[plate_clean] < PLATE_COOLDOWN:
                    status_text = f"{plate_clean} — Sudah diproses"
                else:
                    plate_last_seen[plate_clean] = now
            else:
                plate_last_seen[plate_clean] = now

            valid = re.match(r"^[A-Z]{1,2}\d{1,4}[A-Z]{2,3}$", plate_clean)

            if not valid:
                status_text = f"{plate_clean} — Format Salah"
                color = (0, 0, 255)

            elif conf < CONFIDENCE_THRESHOLD:
                status_text = f"{plate_clean} — Confidence Rendah"
                color = (0, 0, 255)

            else:
                # =============================
                # PROSES VALID PLAT
                # =============================
                if not palang_terbuka:
                    kirim_plat(plate_clean)
                    data = cek_plat(plate_clean)

                    if data:
                        status_text = f"{plate_clean} — Penghuni"
                        color = (0, 255, 0)

                        buka_plang()
                        palang_terbuka = True
                        last_open_time = now

                        catat_masuk(plate_clean, "Penghuni")

                    else:
                        status_text = f"{plate_clean} — Tidak Terdaftar"
                        color = (0, 255, 255)
                        notif_tolak()
                else:
                    status_text = "Palang masih terbuka..."

        else:
            status_text = "Plat tidak terdeteksi"

    # ==================================================
    # DRAW
    # ==================================================
    if bbox:
        x, y, w, h = bbox
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            frame, status_text, (x, max(20, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
        )
    else:
        cv2.putText(frame, status_text, (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Smart Gate AI — ESP32 FINAL", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

running = False
cv2.destroyAllWindows()
print("\n[INFO] SMART GATE AI STOPPED")