import sqlite3
from datetime import datetime
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
import pikepdf
from dotenv import load_dotenv
from email.mime.image import MIMEImage

# Load environment variables
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
PDF_PASSWORD = os.getenv("PDF_PASSWORD", "admin123")

# ================= Log ===================
def tulis_log(pesan):
    """Tulis log aktivitas ke file scheduler_log.txt di folder reports"""
    log_path = os.path.join(os.path.dirname(__file__), "../reports/scheduler_log.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {pesan}\n")

# ================= PDF ===================
def buat_laporan_pdf():
    """Generate PDF harian dari database kendaraan dengan password."""
    try:
        conn = sqlite3.connect("db/smartgate.db")
        df = pd.read_sql_query("SELECT * FROM kendaraan", conn)
        conn.close()

        tanggal = datetime.now().strftime("%Y-%m-%d")
        reports_dir = os.path.join(os.path.dirname(__file__), "../reports")
        os.makedirs(reports_dir, exist_ok=True)
        filename = os.path.join(reports_dir, f"laporan_{tanggal}.pdf")

        if os.path.exists(filename):
            os.remove(filename)

        pdf = SimpleDocTemplate(filename)
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ])
        table.setStyle(style)
        pdf.build([table])

        with pikepdf.open(filename, allow_overwriting_input=True) as pdf_file:
            pdf_file.save(filename, encryption=pikepdf.Encryption(owner=PDF_PASSWORD, user=PDF_PASSWORD, R=4))

        if os.path.exists(filename):
            print(f"✅ PDF berhasil dibuat dan diproteksi: {filename}")
            tulis_log(f"PDF dibuat & diproteksi: {filename}")
            kirim_email_admin(filename)
        else:
            print("❌ PDF gagal dibuat!")
            tulis_log("PDF gagal dibuat!")

    except Exception as e:
        print(f"❌ Error buat laporan PDF: {e}")
        tulis_log(f"Error buat laporan PDF: {e}")

# ================= Email ===================
def kirim_email_admin(file_path):
    """Kirim PDF ke email admin otomatis (HTML + logo lokal)"""
    try:
        msg = EmailMessage()
        msg['Subject'] = "Laporan Harian Smart Gate AI"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL

        tanggal = datetime.now().strftime("%d %B %Y")

        # Path ke logo lokal
        logo_path = os.path.join(os.path.dirname(__file__), "../assets/Logo-UIB.webp")

        # Buat content ID unik buat logo inline
        logo_cid = make_msgid(domain="smartgate.local")

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="text-align: center; padding: 20px;">
                <img src="cid:{logo_cid[1:-1]}" alt="Smart Gate AI" width="120"/>
                <h2 style="color: #0078D7;">Smart Gate AI</h2>
            </div>
            <p>Yth. Admin,</p>
            <p>Berikut terlampir laporan harian sistem <b>Smart Gate AI</b> untuk tanggal <b>{tanggal}</b>.</p>
            <p>File laporan dilindungi dengan password demi keamanan data.</p>
            <p>Terima kasih atas perhatian dan kerjasamanya.</p>
            <br>
            <p>Hormat kami,<br><b>Sistem Smart Gate AI</b></p>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #ccc;">
            <p style="font-size: 12px; color: #888;">Email ini dikirim otomatis oleh sistem Smart Gate AI. Mohon tidak membalas email ini.</p>
        </body>
        </html>
        """

        msg.add_alternative(html_content, subtype='html')

        # Tambah logo inline ke email
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as img:
                msg.get_payload()[0].add_related(img.read(), 'image', 'png', cid=logo_cid)
        else:
            print("⚠️ Logo tidak ditemukan, lanjut tanpa gambar.")

        # Lampirkan file laporan PDF
        with open(file_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(file_path))

        # Kirim email via SMTP Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print(f"📧 PDF berhasil dikirim ke {TO_EMAIL}")
        tulis_log(f"PDF dikirim ke {TO_EMAIL}")

    except Exception as e:
        print(f"❌ Gagal kirim email: {e}")
        tulis_log(f"Gagal kirim email: {e}")
