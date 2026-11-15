import cv2
from ultralytics import YOLO
import requests # Untuk kirim data ke GCP

# 1. Load model OpenVINO (Sangat Cepat di CPU)
model = YOLO('yolo11_openvino_model/')

# 2. Source: IP Tailscale Laptop kamu
# Ganti IP_TAILSCALE dengan IP laptop Asus kamu
url_cam = "rtsp://100.105.95.105:8554/live" 
cap = cv2.VideoCapture(url_cam)

while cap.isOpened():
    success, frame = cap.read()
    if success:
        # Inferensi setiap 3 frame untuk menghemat CPU (Frame Skipping)
        results = model(frame, conf=0.6, verbose=False)
        
        for r in results:
            # Jika terdeteksi 'smoking' (asumsi class 0 adalah rokok)
            if any(box.cls == 0 for box in r.boxes):
                print("⚠️ Pelanggaran Merokok Terdeteksi!")
                
                # KIRIM METADATA KE GCP CLOUD RUN (Bukan Video!)
                # payload = {"loc": "Lab-FKI", "status": "Smoking"}
                # requests.post("URL_CLOUD_RUN_KAMU", json=payload)
                
    else:
        break

cap.release()