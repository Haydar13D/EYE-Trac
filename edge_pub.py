import cv2
import os
import time
import base64
from google.cloud import pubsub_v1

# --- 1. KONFIGURASI ---
# Pastikan file gcp-key.json ada di folder yang sama dengan file ini
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json" 
PROJECT_ID = "breath-6e2a3" 
TOPIC_ID = "smoke-data"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# Inisialisasi Kamera
cap = cv2.VideoCapture(0)

print("🚀 Edge Gateway Aktif. Mengirim data ke Cloud Run via Pub/Sub...")

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # 1. Resize ke 640x480 agar beban upload ringan dan sesuai YOLO
            resized = cv2.resize(frame, (640, 480))
            
            # 2. Encode ke format JPG dengan kualitas 80%
            _, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            
            # 3. KIRIM SEBAGAI BYTES (Jangan di-base64 manual di sini)
            # Library Pub/Sub akan otomatis menangani encoding-nya
            data_to_send = buffer.tobytes()
            
            publisher.publish(topic_path, data=data_to_send)
            
            print(f"✅ Frame terkirim ke Cloud! [{time.strftime('%H:%M:%S')}]") 

            # Tampilan Monitoring Lokal
            cv2.imshow('Edge Monitoring (Tekan Q untuk Keluar)', frame)
        
        # Kirim tiap 1 detik agar tidak membebani kuota dan bandwidth
        if cv2.waitKey(1000) & 0xFF == ord('q'): 
            break

except Exception as e:
    print(f"❌ Error di Edge: {e}")

finally:
    cap.release()
    cv2.destroyAllWindows()