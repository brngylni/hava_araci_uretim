# Resmi Python runtime'ını base imaj olarak kullan
FROM python:3.11-slim
# Projenizdeki Python versiyonuyla eşleştirin

# Ortam değişkenleri
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app # Uygulama için ev dizini

# Çalışma dizinini oluştur ve ayarla
WORKDIR ${APP_HOME}

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# entrypoint script'ini kopyala ve çalıştırılabilir yap
COPY ./entrypoint.sh .
RUN chmod +x ./entrypoint.sh

# Uygulama kodunu kopyala
# .dockerignore dosyası gereksiz dosyaların kopyalanmasını engeller
COPY . .

# Container başladığında entrypoint script'ini çalıştır
ENTRYPOINT ["./entrypoint.sh"]