import os
import base64
import cv2
import numpy as np
import requests
from flask import Flask, request
from ultralytics import YOLO
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime

app = Flask(__name__)

# --- 1. SETUP FIREBASE ---
# Pastikan service_account.json ikut ter-upload saat gcloud builds submit
if not firebase_admin._apps:
    cred = credentials.Certificate("service_account.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'breath-6e2a3.firebasestorage.app'
    })

db = firestore.client()
bucket = storage.bucket()

# --- 2. KONFIGURASI TELEGRAM ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: 
        requests.get(url, timeout=10)
    except Exception as e: 
        print(f"Error Telegram: {e}")

# Load Model YOLOv11 Nano (Ringan untuk Cloud Run)
model = YOLO("yolo11.pt") 

@app.route("/", methods=["POST"])
def index():
    envelope = request.get_json()
    if not envelope or "message" not in envelope:
        return "Bad Request", 400

    pubsub_message = envelope["message"]
    
    if "data" in pubsub_message:
        try:
            # 1. DECODE DATA DARI PUBSUB
            # Data di field 'data' Pub/Sub selalu dalam format base64 string
            img_bytes = base64.b64decode(pubsub_message["data"])
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                # 2. JALANKAN DETEKSI
                results = model.predict(source=frame, conf=0.5, save=False)
                
                for r in results:
                    for box in r.boxes:
                        label = model.names[int(box.cls)]
                        
                        # 3. CEK APAKAH OBJEK ADALAH ROKOK
                        if label == "cigarette":
                            waktu_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                            waktu_teks = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            file_cloud = f"pelanggaran/IMG_{waktu_id}.jpg"
                            
                            # A. Simpan Gambar Hasil Deteksi (dengan Bounding Box)
                            _, img_encoded = cv2.imencode('.jpg', r.plot())
                            blob = bucket.blob(file_cloud)
                            blob.upload_from_string(img_encoded.tobytes(), content_type='image/jpeg')
                            blob.make_public()
                            url_foto = blob.public_url

                            # B. Simpan Metadata ke Firestore
                            db.collection("pelanggaran").add({
                                "akurasi": float(box.conf),
                                "waktu": waktu_teks,
                                "foto_url": url_foto,
                                "lokasi": "Simulasi Edge Laptop",
                                "status": "Belum Ditindak"
                            })

                            # C. Kirim Notifikasi Telegram
                            msg = f"⚠️ PELANGGARAN KTR!\nTerdeteksi: {label}\nAkurasi: {float(box.conf):.2f}\nWaktu: {waktu_teks}\nBukti: {url_foto}"
                            send_telegram_msg(msg)
                            print(f"🔎 DETEKSI BERHASIL: {waktu_teks}")
            else:
                print("❌ ERROR: Frame gagal di-decode (None)")

        except Exception as e:
            print(f"❌ ERROR PROCESSING: {e}")

    return "OK", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))