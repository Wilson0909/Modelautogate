import os
import firebase_admin
from firebase_admin import credentials, firestore

# Ambil folder lokasi file ini (smart_gate_ai/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Buat path lengkap ke serviceAccountKey.json
KEY_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

cred = credentials.Certificate(KEY_PATH)
firebase_admin.initialize_app(cred)

db = firestore.client()