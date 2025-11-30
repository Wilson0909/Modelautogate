import cv2
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

cap = cv2.VideoCapture(0)
time.sleep(2)

if not cap.isOpened():
    print("❌ Kamera tidak terdeteksi!")
    exit()

print("🚗 Smart Gate AI-KELUAR aktif — Tekan 'Q' untuk keluar\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Gagal membaca frame kamera")
        break

    FRAME_COUNT += 1
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    cv2.putText(
        frame, timestamp,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7, (255, 255, 255), 2
    )

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

            # validasi pola plat
            valid = re.match(r'^[A-Z]{1,2}\d{1,4}[A-Z]{1,3}$', plate_clean)

            if valid and conf >= CONFIDENCE_THRESHOLD:

                # kirim setiap deteksi ke LCD Gate Keluar
                kirim_plat_keluar(plate_clean)

                if plate_clean not in vehicles_handled:

                    data = cek_plat(plate_clean)

                    if data:
                        status = "keluar"
                        buka_plang_keluar()
                        catat_keluar(plate_clean, status)
                    else:
                        status = "ditolak"
                        notif_tolak_keluar()
                        catat_keluar(plate_clean, status)

                    vehicles_handled.add(plate_clean)

                else:
                    status_text = f"{plate_clean} — Sudah Diproses"
                    color = (255, 255, 0)

            else:
                status_text = f"{plate_clean} — Tidak Valid"
                color = (0, 0, 255)

        else:
            status_text = "Plat tidak terdeteksi"

        # tampil bounding box + status
        if bbox:
            x, y, w, h = bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, status_text, (x, max(20, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            cv2.putText(frame, status_text, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Smart Gate AI - KELUAR", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
