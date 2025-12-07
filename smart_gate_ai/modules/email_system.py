import os
from email.message import EmailMessage
import smtplib
from datetime import datetime
from email.utils import make_msgid
from dotenv import load_dotenv
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

def tulis_log(pesan):
    print(f"{datetime.now()} | {pesan}")

def kirim_email_admin(file_path, tanggal_laporan):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Laporan Smart Gate AI - {tanggal_laporan}'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL

        # buat content HTML
        logo_cid = make_msgid()
        html_content = f"""
        <html>
          <body>
            <p style="text-align:center;"><img src="cid:{logo_cid[1:-1]}" width="100"></p>
            <p>Yth. Admin,</p>
            <p>Terlampir laporan harian Smart Gate AI tanggal {tanggal_laporan}.</p>
            <p>File PDF dilindungi password.</p>
            <p>Hormat kami,<br>Dataverse System</p>
            <p><i>Email otomatis — jangan dibalas.</i></p>
          </body>
        </html>
        """
        msg.add_alternative(html_content, subtype='html')

        # attach logo
        logo_path = os.path.join(os.path.dirname(__file__), "../assets/logo-2.png")
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                msg.get_payload()[0].add_related(f.read(), 'image', 'png', cid=logo_cid)

        # attach PDF
        with open(file_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(file_path))

        # kirim email
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        tulis_log(f"Email berhasil dikirim ke {TO_EMAIL}")

    except Exception as e:
        tulis_log(f"Email Error: {e}")
