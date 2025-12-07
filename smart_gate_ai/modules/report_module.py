# report_module.py
from datetime import datetime
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import pikepdf
import firebase_admin
from firebase_admin import credentials, firestore
from .email_system import kirim_email_admin, tulis_log

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PASSWORD = os.getenv("PDF_PASSWORD", "admin123")

# ======================== FIREBASE ============================
cred_path = os.path.join(BASE_DIR, "../serviceAccountKey.json")
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ======================== REGISTER FONTS =======================
fonts_dir = os.path.join(BASE_DIR, "../assets/fonts")
pdfmetrics.registerFont(TTFont("Poppins", os.path.join(fonts_dir, "Poppins-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Bold", os.path.join(fonts_dir, "Poppins-Bold.ttf")))

# ======================== PDF GENERATOR =======================
def buat_laporan_pdf(tanggal_laporan=None):
    """
    Buat laporan PDF berdasarkan tanggal tertentu.
    tanggal_laporan: str "YYYY-MM-DD". Jika None, otomatis pakai hari ini.
    """
    try:
        if tanggal_laporan is None:
            tanggal_laporan = datetime.now().strftime("%Y-%m-%d")

        data_list = []

        # ambil data dari logs_masuk
        logs_masuk = db.collection("logs_masuk").stream()
        for doc in logs_masuk:
            d = doc.to_dict()
            waktu_masuk = d.get("waktu_masuk")
            if hasattr(waktu_masuk, "strftime"):
                waktu_masuk_str = waktu_masuk.strftime("%Y-%m-%d %H:%M:%S")
            else:
                waktu_masuk_str = str(waktu_masuk) if waktu_masuk else "-"
            if tanggal_laporan in waktu_masuk_str:
                data_list.append([
                    d.get("id", ""),
                    d.get("plat", ""),
                    d.get("status", ""),
                    waktu_masuk_str,
                    "-"
                ])

        # ambil data dari logs_keluar
        logs_keluar = db.collection("logs_keluar").stream()
        for doc in logs_keluar:
            d = doc.to_dict()
            waktu_keluar = d.get("waktu_keluar")
            if hasattr(waktu_keluar, "strftime"):
                waktu_keluar_str = waktu_keluar.strftime("%Y-%m-%d %H:%M:%S")
            else:
                waktu_keluar_str = str(waktu_keluar) if waktu_keluar else "-"
            if tanggal_laporan in waktu_keluar_str:
                data_list.append([
                    d.get("id", ""),
                    d.get("plat", ""),
                    d.get("status", ""),
                    "-",
                    waktu_keluar_str
                ])

        if not data_list:
            raise Exception(f"Tidak ada log untuk tanggal {tanggal_laporan}.")

        df = pd.DataFrame(data_list, columns=["ID", "Plat", "Status", "Waktu Masuk", "Waktu Keluar"])

        # PATH PDF
        reports_dir = os.path.join(BASE_DIR, "../reports/records/log_kendaraan")
        os.makedirs(reports_dir, exist_ok=True)
        filename = os.path.join(reports_dir, f"laporan_gate_{tanggal_laporan}.pdf")
        if os.path.exists(filename):
            os.remove(filename)

        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []

        # STYLES
        judul_style = ParagraphStyle(name="Judul", fontName="Poppins-Bold", fontSize=18, alignment=1, spaceAfter=6)
        tanggal_style = ParagraphStyle(name="Tanggal", fontName="Poppins", fontSize=12, alignment=1, spaceAfter=20)
        footer_style = ParagraphStyle(name="footer", fontName="Poppins", fontSize=10, alignment=1,
                                      textColor=colors.HexColor("#777777"), leading=14)

        # HEADER
        logo_path = os.path.join(BASE_DIR, "../assets/logo-2.png")
        if os.path.exists(logo_path):
            img = Image(logo_path, width=85, height=85)
            img.hAlign = "CENTER"
            story.append(img)
            story.append(Spacer(1, 10))

        story.append(Paragraph("Laporan Harian Smart Gate AI", judul_style))
        story.append(Paragraph(f"Tanggal Laporan: {tanggal_laporan}", tanggal_style))

        # TABLE
        table = Table([df.columns.tolist()] + df.values.tolist(),
                      colWidths=[2.3*cm, 3*cm, 2.5*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#795FFC")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Poppins-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 11),
            ("FONTNAME", (0,1), (-1,-1), "Poppins"),
            ("FONTSIZE", (0,1), (-1,-1), 10),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D2D2D2")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F5F0FF"), colors.white])
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # FOOTER
        footer = Paragraph("Laporan ini dihasilkan otomatis oleh Smart Gate AI.<br/>", footer_style)
        story.append(footer)

        doc.build(story)

        # ENCRYPT PDF
        with pikepdf.open(filename, allow_overwriting_input=True) as pdf:
            pdf.save(filename, encryption=pikepdf.Encryption(user=PDF_PASSWORD, owner=PDF_PASSWORD, R=4))

        tulis_log(f"PDF laporan dibuat untuk tanggal {tanggal_laporan}.")
        print("PDF dibuat:", filename)

        # KIRIM EMAIL
        kirim_email_admin(filename)

    except Exception as e:
        tulis_log(f"PDF Error: {e}")
        print("❌ PDF ERROR:", e)
