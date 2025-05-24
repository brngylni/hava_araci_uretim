#!/bin/sh

# Scriptin herhangi bir komutta hata alması durumunda çıkmasını sağla
set -e

# Veritabanı hazır olana kadar bekleme (opsiyonel ama önerilir)
# docker-compose.yml'deki depends_on, sadece container'ın başlamasını bekler,
# servisin (örn: postgres) tam olarak hazır olmasını garantilemez.
# Bu yüzden, DB_HOST ve DB_PORT ortam değişkenlerini kullanarak bir bekleme mekanizması eklenebilir.
# Basitlik için, PostgreSQL'in varsayılan olarak çabuk başlayacağını varsayıyoruz.
# Daha karmaşık bir bekleme için:
# until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
#   >&2 echo "Postgres is unavailable - sleeping"
#   sleep 1
# done
# >&2 echo "Postgres is up - continuing"

echo "Applying database migrations..."
python manage.py migrate --noinput

# Statik dosyaları toplama (Nginx sunacaksa)
# Eğer Django admin paneli veya WhiteNoise kullanılıyorsa gereklidir.
# Canlı ortamda DEBUG=False olacağı için Django statik dosyaları sunmaz.
# Bu dosyaların Nginx tarafından erişilebilir bir yerde olması gerekir.
# Dockerfile'da bir VOLUME tanımlayıp Nginx container'ı ile paylaşılabilir.
# Veya build sırasında Nginx imajına kopyalanabilir.
# Şimdilik WhiteNoise kullanmadığımızı ve admin statiklerinin Django tarafından
# (Gunicorn üzerinden) sunulabileceğini varsayalım veya Nginx konfigürasyonunda handle edelim.
# Eğer Nginx statikleri sunacaksa:
# python manage.py collectstatic --noinput --clear
# echo "Static files collected."

echo "Starting Gunicorn..."
# `hava_araci_uretim_app` sizin ana proje klasörünüzün adı olmalı (wsgi.py'nin olduğu yer)
# --workers: Genellikle 2 * CPU_CORES + 1 olarak ayarlanır.
# --timeout: Uzun süren istekler için timeout süresi (saniye cinsinden).
exec gunicorn apps.hava_araci_uretim_app.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --log-level=info \
    --access-logfile '-' \
    --error-logfile '-'
# '-' logları stdout/stderr'e yönlendirir, Docker logları için iyidir.