from ultralytics import YOLO
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import cv2
import re
import numpy as np

# === Load model lokal ===
yolo_model = YOLO(r"/Users/wilsonzeng/Documents/smart_gate_ai/smart_gate_ai/models/license_plate_detector.pt")
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
ocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")

device = "cuda" if torch.cuda.is_available() else "cpu"
ocr_model.to(device)

def ocr_trocr(image):
    """
    Melakukan OCR menggunakan TrOCR pretrained model
    """
    if image.size == 0:
        return ""
    
    # Konversi BGR ke RGB dan ke PIL Image
    image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)

    # Generate teks
    generated_ids = ocr_model.generate(pixel_values)
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    # Bersihkan teks
    text = re.sub(r'[^A-Z0-9 ]', '', text.upper())
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def recognize_plate(frame):
    """
    Deteksi plat menggunakan YOLO + OCR TrOCR
    Mengembalikan:
        plate (str) : teks plat
        conf (float) : confidence YOLO
        bbox (tuple) : (x, y, w, h)
    """
    try:
        # 1️⃣ Deteksi plat nomor dengan YOLO
        results = yolo_model(frame, verbose=False)
        detections = results[0].boxes.data.cpu().numpy()

        if len(detections) == 0:
            return None, 0.0, None

        # Ambil deteksi dengan confidence tertinggi
        best = max(detections, key=lambda x: x[4])
        x1, y1, x2, y2, conf, cls = best
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        # 2️⃣ Crop area plat
        plate_img = frame[y1:y2, x1:x2]
        if plate_img.size == 0:
            return None, 0.0, None

        # 3️⃣ OCR dengan TrOCR
        plate_text = ocr_trocr(plate_img)

        # 4️⃣ Bounding box
        bbox = (x1, y1, x2 - x1, y2 - y1)

        return plate_text, float(conf), bbox

    except Exception as e:
        print(f"[ERROR OCR] {e}")
        return None, 0.0, None
