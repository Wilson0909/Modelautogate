# email_system.py
import os
from email.message import EmailMessage
import smtplib
from datetime import datetime

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # pastikan sesuai .env
TO_EMAIL = os.getenv("TO_EMAIL")

def tulis_log(pesan):
    print(f"{datetime.now()} | {pesan}")

def kirim_email_admin(file_path, tanggal_laporan=None):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Laporan Harian Smart Gate AI - {tanggal_laporan or ""}'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL

        # isi email
        msg.set_content(f"""Yth. Admin,

        Terlampir laporan harian Smart Gate AI tanggal {tanggal_laporan or datetime.now().strftime('%d %B %Y')}.

        File PDF dilindungi password.

        Hormat kami,
        Smart Gate AI Team

        Email otomatis — jangan dibalas.
        """)

        # attach PDF
        with open(file_path, 'rb') as f:
            msg.add_attachment(f.read(),
                               maintype='application',
                               subtype='pdf',
                               filename=os.path.basename(file_path))

        # Kirim email
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        tulis_log(f"Email berhasil dikirim ke {TO_EMAIL}")

    except Exception as e:
        tulis_log(f"Email Error: {e}")
