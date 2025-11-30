import cv2
from smart_gate_ai.modules.ocr_module import recognize_plate

img_path = r"D:\KULIAH\Sem 5\EXPO PROJECT\smart_gate_ai\9fcb085c-305e-49c9-ab27-1746c1d8f6ec.jpeg"
img = cv2.imread(img_path)

if img is None:
    print("❌ Gambar tidak terbaca, cek path-nya.")
else:
    plate, conf, bbox = recognize_plate(img)
    print(f"✅ Detected: {plate} | Confidence: {conf*100:.2f}%")

    if bbox:
        x, y, w, h = bbox
        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
        cv2.putText(img, plate or "UNKNOWN", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.imshow("Detected Plate", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
