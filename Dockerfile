# 1. Gunakan Python 3.9-slim
FROM python:3.9-slim

# 2. Update dan instal library pendukung OpenCV terbaru
# Kita ganti libgl1-mesa-glx menjadi libgl1
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set folder kerja
WORKDIR /app

# 4. Copy file (Hanya yang penting agar build lebih cepat)
COPY requirements.txt .
COPY main.py .
COPY service_account.json .
COPY yolo11.pt .

# 5. Instal library Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. Set Port
ENV PORT 8080

# 7. Jalankan aplikasi
CMD ["python", "main.py"]   