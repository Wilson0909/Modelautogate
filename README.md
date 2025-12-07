# Smart Gate AI (Model_Autogate)

## Summary

**Smart Gate AI** adalah proyek sistem gerbang pintar yang menggunakan teknologi deteksi objek dan pembacaan plat nomor kendaraan secara otomatis. Sistem ini terintegrasi dengan Firebase, aplikasi mobile, dan perangkat IoT seperti ESP32 CAM dan servo.

---

## Model yang Digunakan

- **YOLO (You Only Look Once)**:  
  Metode deteksi objek cepat dan akurat. Digunakan untuk mendeteksi plat nomor kendaraan.

- **OCR (Optical Character Recognition)**:  
  Menggunakan **Pytesseract** untuk membaca teks pada gambar plat nomor.

---

## Algoritma & Sistem

1. **Fuzzy Logic**:  
   Mengatasi threshold confidence, contohnya hanya menerima plat dengan confidence ≥ 0.60.  

2. **Generative Algorithm**:  
   Membuat laporan harian yang dikirim otomatis ke email admin.  

3. **Expert System**:  
   - Jika kendaraan terdaftar → servo membuka palang.  
   - Jika tidak terdaftar → palang tetap tertutup / reject.  

4. **Knowledge Base Agent**:  
   Membaca database kendaraan yang terdaftar untuk membuka palang.  

5. **Learning Agent**:  
   Belajar mengenali plat nomor baru yang sebelumnya belum dikenal.  

---

## Training Model

- Menggunakan **pretrained YOLO model** dari sumber luar.https://github.com/Muhammad-Zeerak-Khan/Automatic-License-Plate-Recognition-using-YOLOv8   
- Menambahkan bounding box dan OCR untuk membaca plat.  

---

## Hardware / Arduino Setup

- ESP32 CAM  
- Servo motor  
- Arduino / Breadboard  
- LCD Display  

---

## Cara Kerja Sistem

1. Kamera ESP32 CAM terhubung ke IP Cam via WiFi.  
2. Sistem dijalankan dan kamera membaca plat kendaraan.  
3. Jika confidence > 0.60 → palang terbuka (indikator hijau), dan logs masuk/keluar diupdate ke Firebase.  
4. Jika plat tidak terdaftar → palang tertutup (indikator merah 10 detik).  

---

## Aplikasi Mobile

- **Flutter-based** aplikasi untuk pengguna dan admin:  
  - **User**:  
    - Tambah kendaraan  
    - Cek kendaraan masuk/keluar  
    - Lihat pengumuman  
  - **Admin**:  
    - Tambah pengumuman  
    - Tambah user  
    - Lihat list kendaraan dan logs  

---

## Status

Sistem sudah berjalan dengan integrasi hardware, mobile app, model AI, dan email reporting otomatis.
