from firebase_init import db

# test write
db.collection("test_connection").add({"status": "connected"})

print("OK!")
