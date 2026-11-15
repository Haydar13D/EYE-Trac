import cv2
from ultralytics import YOLO
import time
import requests
from datetime import datetime
import os

# --- 1. KONFIGURASI TELEGRAM ---
# Tips: Gunakan BotFather untuk buat Bot baru jika ingin memisahkan log
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

def send_telegram_alert(photo_path, caption):
    """Mengirim foto dan caption ke Telegram sebagai pengganti Firebase"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            payload = {
                'chat_id': CHAT_ID,
                'caption': caption,
                'parse_mode': 'Markdown' # Biar teks lebih rapi
            }
            files = {'photo': photo}
            response = requests.post(url, data=payload, files=files)
            if response.status_code == 200:
                print("🚀 Alert terkirim ke Telegram!")
            else:
                print(f"❌ Gagal kirim: {response.text}")
    except Exception as e:
        print(f"⚠️ Error Telegram: {e}")

# --- 2. MULAI DETEKSI ---
model = YOLO("yolo11.pt") 
cap = cv2.VideoCapture(0)
last_notification_time = 0
cooldown = 15 # Jeda antar notifikasi

print("🛡️ EYE-TRAC Local Mode: Active (Saving to Telegram)...")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    # Optimasi: Proses setiap frame, tapi hanya kirim jika conf tinggi
    results = model(frame, conf=0.7)
    
    for r in results:
        for box in r.boxes:
            label = model.names[int(box.cls)]
            
            if label == "cigarette":
                current_time = time.time()
                if current_time - last_notification_time > cooldown:
                    
                    waktu_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                    waktu_teks = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    file_lokal = f"vandal_{waktu_id}.jpg"
                    
                    # A. Simpan Gambar Lokal dengan Anotasi (Hasil Deteksi)
                    annotated_frame = r.plot()
                    cv2.imwrite(file_lokal, annotated_frame)
                    
                    # B. Buat Narasi Metadata (Pengganti Firestore)
                    caption = (
                        f"⚠️ *PELANGGARAN TERDETEKSI*\n\n"
                        f"👤 *Objek:* Merokok\n"
                        f"📍 *Lokasi:* Lab Informatika UMS\n"
                        f"⏱️ *Waktu:* {waktu_teks}\n"
                        f"🎯 *Akurasi:* {float(box.conf):.2f}\n"
                        f"Status: _Terekam di Local Storage_"
                    )
                    
                    # C. Kirim ke Telegram
                    send_telegram_alert(file_lokal, caption)
                    
                    # D. Cleanup (Hapus file lokal setelah kirim agar disk tidak penuh)
                    # os.remove(file_lokal) 
                    
                    last_notification_time = current_time

    cv2.imshow("EYE-TRAC Local Monitoring", results[0].plot())
    if cv2.waitKey(1) & 0xFF == ord("q"): break

cap.release()
cv2.destroyAllWindows()