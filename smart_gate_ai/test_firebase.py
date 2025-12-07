import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("smart_gate_ai/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
print("OK:", list(db.collection("logs_masuk").limit(1).stream()))
