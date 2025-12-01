import cv2
import threading
import urllib.request
import numpy as np
import time
import re

from smart_gate_ai.modules.ocr_module import recognize_plate
from smart_gate_ai.modules.arduino_module import buka_plang, notif_tolak, kirim_plat
from smart_gate_ai.modules.database_module import cek_plat, catat_masuk

ESP32_IP = "10.224.25.153"
STREAM_URL = f"http://{ESP32_IP}/capture"

CONFIDENCE_THRESHOLD = 0.60
PROCESS_EVERY = 3

frame_lock = threading.Lock()
latest_frame = None
running = True
frame_count = 0
vehicles_handled = set()


# ================================
# THREAD CAMERA ESP32
# ================================
def camera_thread():
    global latest_frame, running

    print("[THREAD] Kamera ESP32 berjalan...")

    while running:
        try:
            resp = urllib.request.urlopen(STREAM_URL, timeout=1)
            img_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is not None:
                with frame_lock:
                    latest_frame = frame

        except Exception as e:
            print("❌ Kamera error:", e)
            time.sleep(0.1)


thread = threading.Thread(target=camera_thread)
thread.start()

print("[INFO] Smart Gate AI berjalan (THREAD MODE)")
print("Tekan Q untuk keluar.\n")


# ================================
# MAIN LOOP OCR
# ================================
while True:
    with frame_lock:
        if latest_frame is None:
            continue
        frame = latest_frame.copy()

    frame_count += 1
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    cv2.putText(frame, timestamp, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if frame_count % PROCESS_EVERY == 0:

        # ========== TRY OCR ==========
        try:
            plate, conf, bbox = recognize_plate(frame)
        except Exception as e:
            print(f"[OCR ERROR] {e}")
            plate, conf, bbox = None, 0, None

        status_text = "Mendeteksi plat..."
        color = (0, 0, 255)

        # =====================================
        #   JIKA ADA HASIL OCR
        # =====================================
        if plate:
            plate_clean = re.sub(r'\s+', '', plate.upper())
            print(f"[{timestamp}] OCR: {plate_clean} | Conf: {conf:.2f}")

            # ========== VALIDASI FORMAT ==========
            if len(plate_clean) < 7:
                status_text = f"{plate_clean} — Plat Tidak Lengkap"

            else:
                valid = re.match(r'^[A-Z]{1,2}\d{1,4}[A-Z]{1,3}$', plate_clean)
                suffix = re.findall(r'[A-Z]+$', plate_clean)[0] if valid else ""

                if not valid or len(suffix) < 2:
                    status_text = f"{plate_clean} — Format Tidak Lengkap"

                # --------------------------------------
                #      VALID OCR → BOLEH CONTINUE
                # --------------------------------------
                elif conf >= CONFIDENCE_THRESHOLD:

                    # Kirim ke Arduino untuk OLED/lainnya
                    kirim_plat(plate_clean)

                    # Cek Firebase
                    data = cek_plat(plate_clean)

                    # =====================================
                    #   EXACT MATCH → PENGHUNI
                    # =====================================
                    if data:
                        if plate_clean not in vehicles_handled:
                            buka_plang()
                            status_text = f"{plate_clean} — Penghuni"
                            color = (0, 255, 0)

                            catat_masuk(plate_clean, "Penghuni")
                            vehicles_handled.add(plate_clean)

                        else:
                            status_text = f"{plate_clean} — Sudah Diproses"
                            color = (255, 255, 0)

                    # =====================================
                    #   NOT FOUND → TAMU TIDAK TERDAFTAR
                    # =====================================
                    else:
                        if plate_clean not in vehicles_handled:
                            notif_tolak()
                            status_text = f"{plate_clean} — Tidak Terdaftar"
                            color = (0, 255, 255)

                        else:
                            status_text = f"{plate_clean} — Sudah Diproses"
                            color = (255, 255, 0)

                else:
                    status_text = f"{plate_clean} — Confidence Rendah"

        else:
            status_text = "Plat tidak terdeteksi"

        # ========== DRAW BOX ==========
        if bbox:
            x, y, w, h = bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, status_text, (x, max(20, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            cv2.putText(frame, status_text, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Smart Gate AI — ESP32CAM", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


running = False
thread.join()
cv2.destroyAllWindows()