import cv2
import numpy as np
import urllib.request
import re
import time
from smart_gate_ai.modules.ocr_module import recognize_plate
from smart_gate_ai.modules.arduino_module import (
    buka_plang_keluar,
    notif_tolak_keluar,
    kirim_plat_keluar
)
from smart_gate_ai.modules.database_module import cek_plat, catat_keluar

CONFIDENCE_THRESHOLD = 0.60
PROCESS_EVERY = 3
FRAME_COUNT = 0
vehicles_handled = set()

ESP32_IP = "10.224.25.4"   # <-- GANTI KALAU PAKAI IP KAMERA LAIN
SNAPSHOT_URL = f"http://{ESP32_IP}/capture"

print("[INFO] Mode SNAPSHOT aktif — Gate Keluar mengambil gambar dari /capture...")
print("Tekan Q untuk keluar.\n")

while True:
    try:
        # Ambil foto dari ESP32-CAM
        resp = urllib.request.urlopen(SNAPSHOT_URL, timeout=2)
        img_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"❌ Gagal ambil gambar dari ESP32-CAM: {e}")
        time.sleep(1)
        continue

    FRAME_COUNT += 1
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    cv2.putText(frame, timestamp, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if FRAME_COUNT % PROCESS_EVERY == 0:

        try:
            plate, conf, bbox = recognize_plate(frame)
        except Exception as e:
            print(f"⚠️ Error OCR: {e}")
            plate, conf, bbox = None, 0, None

        status_text = "Mendeteksi plat..."
        color = (0, 0, 255)

        if plate:
            plate_clean = re.sub(r'\s+', '', plate.upper())
            print(f"[{timestamp}] OCR: '{plate_clean}' | Conf: {conf:.2f}")

            valid = re.match(r'^[A-Z]{1,2}\d{1,4}[A-Z]{1,3}$', plate_clean)

            if valid and conf >= CONFIDENCE_THRESHOLD:

                kirim_plat_keluar(plate_clean)

                if plate_clean not in vehicles_handled:

                    data = cek_plat(plate_clean)

                    if data:
                        status_text = f"{plate_clean} — Keluar"
                        color = (0, 255, 0)
                        buka_plang_keluar()
                        catat_keluar(plate_clean, "keluar")
                    else:
                        status_text = f"{plate_clean} — Tidak Terdaftar"
                        color = (0, 255, 255)
                        notif_tolak_keluar()
                   
                else:
                    status_text = f"{plate_clean} — Sudah Diproses"
                    color = (255, 255, 0)

            else:
                status_text = f"{plate_clean} — Format Tidak Valid"
                color = (0, 0, 255)

        else:
            status_text = "Plat tidak terdeteksi"

        if bbox:
            x, y, w, h = bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, status_text, (x, max(20, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            cv2.putText(frame, status_text, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Smart Gate AI - KELUAR (Snapshot Mode)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()