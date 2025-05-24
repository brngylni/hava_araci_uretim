Elbette! Projenizin son haline ve konuştuğumuz tüm detaylara göre kapsamlı bir `README.md` dökümantasyonu oluşturalım. Bu dökümantasyon, projeyi yeni alan birinin veya gelecekte sizin kolayca anlayıp çalıştırabilmesi için gerekli tüm bilgileri içerecektir.

---

# Hava Aracı Üretim Uygulaması API - Proje Dökümantasyonu

## 1. Projeye Genel Bakış

Bu proje, bir hava aracı üretim ve envanter yönetim sistemini simüle eden, Django ve Django REST Framework (DRF) tabanlı bir backend API uygulamasıdır. Sistem, farklı hava aracı modelleri için gerekli parçaların üretimini, bu parçaların takibini, takımlar arası iş dağılımını ve son olarak uyumlu parçaların birleştirilerek hava araçlarının montajını yönetir.

### 1.1. Amaç

Projenin temel amacı, karmaşık bir üretim sürecini modelleyerek, aşağıdaki yeteneklere sahip bir API altyapısı sunmaktır:

*   Personel ve üretim/montaj takımlarının yönetimi.
*   Parça tipleri (Kanat, Gövde vb.) ve uçak modellerinin (TB2, AKINCI vb.) tanımlanması.
*   Her bir parça tipinden sorumlu üretim takımlarının, kendi sorumluluk alanlarındaki parçaları (belirli bir uçak modeliyle uyumlu olarak) üretmesi.
*   Üretilen parçaların envanterde takibi (stok durumu, seri numarası).
*   Parçaların geri dönüşüme gönderilmesi (silinmesi).
*   Montaj Takımı tarafından, stoktaki uyumlu ve doğru tipteki parçaların bir araya getirilerek belirli bir modelde hava aracı monte edilmesi.
*   Monte edilen uçakların ve kullanılan parçaların kaydının tutulması.
*   Envanterdeki eksik parçalar için uyarı mekanizması.
*   Rol bazlı yetkilendirme ile farklı kullanıcı gruplarının (Admin, Üretim Takımı Üyesi, Montaj Takımı Üyesi) yetkilerinin sınırlandırılması.

### 1.2. Temel İşlevler

*   **Kullanıcı Yönetimi:** Personel kaydı, sisteme giriş (token tabanlı kimlik doğrulama), profil yönetimi (takım ataması).
*   **Takım Yönetimi (Admin):** Üretim ve montaj takımlarının oluşturulması ve yönetimi. Üretim takımlarının sorumlu olduğu parça tiplerinin belirlenmesi.
*   **Referans Veri Yönetimi (Admin/Data Migration):** Parça tipleri ve uçak modelleri gibi temel verilerin sisteme tanımlanması.
*   **Parça Üretimi:** Yetkili üretim takımlarının kendi sorumlu oldukları parça tiplerinden, belirli bir uçak modeliyle uyumlu parçalar üretmesi.
*   **Parça Envanteri:** Üretilen parçaların listelenmesi, filtrelenmesi, detaylarının görülmesi.
*   **Parça Geri Dönüşümü:** Üreten takım tarafından parçaların geri dönüşüme gönderilmesi (silinmesi).
*   **Uçak Montajı:** Montaj Takımı tarafından, gerekli tüm parçaların (doğru tip, doğru model uyumu, stokta olma durumu kontrol edilerek) birleştirilip yeni bir uçağın monte edilmesi.
*   **Monte Edilmiş Uçak Listesi:** Sistemdeki tüm monte edilmiş uçakların listelenmesi.
*   **Eksik Parça Kontrolü:** Belirli bir uçak modeli için montajda gerekli olan temel parçaların envanterdeki stok durumunun kontrol edilmesi.

## 2. Teknoloji Stack'i ve Kütüphaneler

*   **Backend:**
    *   Python (3.11+ önerilir)
    *   Django (Son LTS veya güncel stabil versiyon)
    *   Django REST Framework (DRF): API geliştirme için.
    *   psycopg2-binary: PostgreSQL veritabanı bağlantısı için.
    *   Gunicorn: WSGI HTTP sunucusu (canlı ortam için).
*   **Veritabanı:** PostgreSQL (15+ önerilir)
*   **API Dökümantasyonu:**
    *   drf-spectacular: OpenAPI 3 şeması üretimi ve Swagger UI/ReDoc entegrasyonu.
*   **Test:**
    *   Django Test Framework (`TestCase`, `APITestCase`)
    *   factory_boy: Test verisi üretimi için.
    *   Coverage.py: Kod kapsamı analizi için.
*   **Filtreleme (API):**
    *   django-filter: DRF için gelişmiş filtreleme.
    *   rest_framework_datatables: Server-side DataTables entegrasyonu için (kullanıldıysa).
*   **CORS Yönetimi:**
    *   django-cors-headers: Cross-Origin Resource Sharing başlıklarını yönetmek için.
*   **Ortam Değişkenleri Yönetimi (Django):**
    *   django-environ: `.env` dosyalarından ve ortam değişkenlerinden ayarları okumak için.
*   **Containerization:**
    *   Docker
    *   Docker Compose
*   **Frontend (React Uygulaması):**
    *   React (Vite ile oluşturulmuş)
    *   JavaScript (ES6+)
    *   Tailwind CSS: Stil için.
    *   react-router-dom: Sayfa yönlendirmeleri için.
    *   axios: API istekleri için.
    *   react-data-table-component: Veri tabloları için (server-side data destekli).
    *   (jQuery ve DataTables.net, eğer `datatables.net-react` yerine doğrudan jQuery tabanlı DataTables kullanıldıysa)

## 3. Proje Yapısı

Proje, Django uygulamalarını içeren bir `backend` klasörü ve React uygulamasını içeren bir `frontend` klasörü ile yapılandırılmıştır. Nginx konfigürasyonu için ayrı bir `nginx` klasörü bulunur.

```
hava_araci_uretim/      (Proje Kök Dizini)
├── hava_araci_uretim/            (Django Projesi)
│   ├── apps/           (Django Uygulamaları)
    │   ├── hava_araci_uretim_app/ (Ana Django proje ayarları)
│   │   ├── core/       (Temel modeller, izinler, serializer'lar)
│   │   ├── envanter/   (Parça, Parça Tipi, Uçak Modeli modelleri, API'leri)
│   │   ├── montaj/     (Monte Edilmiş Uçak modelleri, API'leri)
│   │   ├── uretim/     (Takım modelleri, API'leri)
│   │   └── users/      (UserProfile modeli, User API'leri, sinyaller)
│   │
│   ├── manage.py
│   ├── Dockerfile        # Django için
│   ├── entrypoint.sh     # Django container başlangıç script'i
│   └── requirements.txt  # Python bağımlılıkları
├── frontend/           (React Projesi)
│   ├── public/
│   ├── src/
│   │   ├── api/          (axios instance, servis fonksiyonları)
│   │   ├── assets/
│   │   ├── components/   (Layout, ortak UI bileşenleri)
│   │   ├── contexts/     (AuthContext vb.)
│   │   ├── pages/        (Her sayfa için ana React bileşenleri)
│   │   ├── App.jsx
│   │   ├── index.css     (Global stiller, Tailwind direktifleri)
│   │   └── main.jsx
│   ├── Dockerfile          # React build ve Nginx için
│   ├── package.json
│   ├── vite.config.js    # Vite ayarları (proxy dahil)
│   └── .env              # Frontend'e özel ortam değişkenleri (VITE_ ile başlar)
├── nginx/                # Nginx konfigürasyonu
│   └── default.conf
├── .dockerignore         # Docker build context'inden hariç tutulacaklar
├── .env                  # Docker Compose için ortam değişkenleri (proje kökünde)
├── docker-compose.yml    # Tüm servisleri yönetir
└── .gitignore            # Git tarafından takip edilmeyecekler
└── README.md             # Bu dosya
```

## 4. Kurulum ve Çalıştırma (Docker Compose ile - Önerilen)

Bu yöntem, tüm bağımlılıkları (Python, Node.js, PostgreSQL, Nginx) Docker container'ları içinde yönetir ve tek bir komutla tüm sistemi ayağa kaldırır.

### 4.1. Ön Koşullar
*   Docker Desktop (Windows/macOS) veya Docker Engine + Docker Compose (Linux) kurulu olmalıdır.
*   Git kurulu olmalıdır.

### 4.2. Kurulum Adımları
1.  **Projeyi Klonlayın:**
    ```bash
    git clone <repository_url>
    cd hava_araci_uretim
    ```
2.  **`.env` Dosyasını Oluşturun:**
    Proje kök dizininde (`docker-compose.yml` ile aynı yerde) `.env.example` (eğer varsa) dosyasını kopyalayarak veya sıfırdan bir `.env` dosyası oluşturun. Aşağıdaki değişkenleri kendi ortamınıza göre veya varsayılan değerlerle doldurun:
    ```env
    # .env (Proje Kök Dizini)
    DEBUG=0  # Canlı için 0, geliştirme için 1 (DEBUG=1 ise Django detaylı hata gösterir)
    SECRET_KEY=your_very_strong_and_secret_django_key_here 
    ALLOWED_HOSTS=localhost,127.0.0.1,api,nginx # Nginx ve API servis adları da eklenebilir

    # PostgreSQL Ayarları (docker-compose.yml'deki environment ile eşleşmeli)
    DB_ENGINE=django.db.backends.postgresql
    DB_NAME=hava_araci_db_docker
    DB_USER=docker_user
    DB_PASSWORD=supersecretpassword 
    DB_HOST=db # docker-compose.yml'deki PostgreSQL servis adı
    DB_PORT=5432
    ```
    **NOT:** `SECRET_KEY` için güçlü ve eşsiz bir anahtar üretin.

3.  **Docker Servislerini Başlatın:**
    Proje kök dizininde terminali açın ve aşağıdaki komutu çalıştırın:
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: İlk çalıştırmada veya Dockerfile'larda değişiklik yapıldığında imajları (yeniden) oluşturur.
    *   `-d`: Servisleri arka planda (detached modda) başlatır.
    Bu işlem biraz zaman alabilir, özellikle ilk build sırasında.

4.  **Veritabanı Migration'larını ve Data Migration'larını Uygulama:**
    `backend/entrypoint.sh` script'i `python manage.py migrate --noinput` komutunu otomatik olarak çalıştırmalıdır. Bu, veritabanı şemasını oluşturacak ve data migration'lar (varsayılan parça tipleri, takımlar, kullanıcılar) aracılığıyla başlangıç verilerini yükleyecektir.
    Eğer bu otomatik olarak çalışmazsa veya kontrol etmek isterseniz, ayrı bir terminalde:
    ```bash
    docker-compose exec api python manage.py migrate
    ```

5.  **Süper Kullanıcı Oluşturma (Eğer Data Migration ile Oluşturulmadıysa):**
    Eğer data migration ile varsayılan bir admin kullanıcısı oluşturmadıysanız veya farklı bir tane oluşturmak isterseniz:
    ```bash
    docker-compose exec api python manage.py createsuperuser
    ```
    Data migration ile oluşturulan varsayılan admin kullanıcısının bilgileri (eğer migration'da belirtilmişse) dökümantasyonun ilgili bölümünde yer almalıdır.

### 4.3. Uygulamaya Erişim
*   **Frontend Arayüzü:** Tarayıcınızda `http://localhost` (veya `http://localhost:80` Nginx portu) adresine gidin.
*   **API Dökümantasyonu (Swagger UI):** `http://localhost/api/v1/schema/swagger-ui/`
*   **Django Admin Paneli:** `http://localhost/admin/` (Nginx konfigürasyonunuzun `/admin/` isteklerini `api` servisine yönlendirdiğinden emin olun. Genellikle `/api/v1/admin/` daha standarttır veya Nginx'te `/admin` için ayrı bir `location` bloğu gerekir.)

### 4.4. Servisleri Durdurma
```bash
docker-compose down
```
Verilerin kalıcı olması için `postgres_data_volume` adlı bir volume kullanılmıştır. `docker-compose down -v` komutu bu volume'ü de siler (dikkatli olun!).

## 5. Data Migration ile Oluşturulan Varsayılan Veriler

Proje ilk kez `migrate` edildiğinde, aşağıdaki data migration'lar çalışarak sisteme başlangıç verilerini yükler:

*   **`envanter.XXXX_populate_initial_part_types`:**
    *   Oluşturulan Parça Tipleri (Kod Adı / Okunabilir Ad):
        *   `KANAT` / "Kanat"
        *   `GOVDE` / "Gövde"
        *   `KUYRUK` / "Kuyruk"
        *   `AVIYONIK` / "Aviyonik"
*   **`envanter.YYYY_populate_initial_aircraft_models` (Eğer böyle bir migration yazdıysanız):**
    *   Oluşturulan Uçak Modelleri: "TB2", "TB3", "AKINCI", "KIZILELMA"
*   **`uretim.ZZZZ_populate_initial_teams`:**
    *   Oluşturulan Takımlar ve Sorumlu Oldukları Parça Tipleri:
        *   "Kanat Takımı" (`name='KANAT'`), Sorumlu: KANAT PartType
        *   "Gövde Takımı" (`name='GOVDE'`), Sorumlu: GOVDE PartType
        *   "Kuyruk Takımı" (`name='KUYRUK'`), Sorumlu: KUYRUK PartType
        *   "Aviyonik Takımı" (`name='AVIYONIK'`), Sorumlu: AVIYONIK PartType
        *   "Montaj Takımı" (`name='MONTAJ'`), Sorumlu: Yok (None)
*   **`users.AAAA_create_default_team_users` (Eğer böyle bir migration yazdıysanız):**
    *   Bu migration, her bir yukarıdaki takım için varsayılan bir kullanıcı oluşturur.
    *   **Kullanıcı Adı Formatı:** `[takım_kodu_küçük_harf]` (örn: `kanat`, `govde`, `montaj`)
    *   **Şifre Formatı:** `[kullanıcı_adı]123` (örn: `kanat123`, `montaj123`)
    *   **E-posta Formatı:** `[kullanıcı_adı]@example.com`
    *   Bu kullanıcılar otomatik olarak ilgili takımlara atanır.
    *   **Örnek Kullanıcılar:**
        *   Kullanıcı Adı: `kanat`, Şifre: `kanat123`, Takımı: Kanat Takımı
        *   Kullanıcı Adı: `govde`, Şifre: `govde123`, Takımı: Gövde Takımı
        *   Kullanıcı Adı: `aviyonik`, Şifre: `aviyonik123`, Takımı: Aviyonik Takımı
        *   Kullanıcı Adı: `kuyruk`, Şifre: `kuyruk123`, Takımı: Kuyruk Takımı
        *   Kullanıcı Adı: `montaj`, Şifre: `montaj123`, Takımı: Montaj Takımı
*   **`users.BBBB_create_dev_superuser` (Eğer böyle bir migration yazdıysanız):**
    *   Geliştirme için özel bir süper kullanıcı oluşturur.
    *   Kullanıcı Adı: `root` (veya migration'da belirttiğiniz)
    *   Şifre: `root123` (veya migration'da belirttiğiniz)
    *   **Bu kullanıcıyı canlı ortamda KULLANMAYIN ve ilk girişten sonra şifresini DEĞİŞTİRİN!**

## 6. API Kullanımı ve Temel İş Akışları

1.  **Giriş Yapma:**
    *   Frontend'deki Login sayfasını kullanın veya `/api/v1/users/login/` endpoint'ine `username` ve `password` ile `POST` isteği gönderin.
    *   Yanıt olarak gelen `token`'ı sonraki yetkili istekler için saklayın.

2.  **Personel (Kullanıcı) Kendi Takımını Atama/Değiştirme:**
    *   Giriş yapmış kullanıcı, frontend'deki "Profilim" (veya benzeri) sayfasından `/api/v1/users/profiles/my_profile/` endpoint'ine `PATCH` isteği ile `team` (takım ID'si) göndererek kendi takımını güncelleyebilir.

3.  **Parça Üretme (Üretim Takımı Üyesi):**
    *   Kullanıcı, sorumlu olduğu parça tipinden bir parça üretmek için frontend'deki "Yeni Parça Üret" formunu kullanır.
    *   Bu form, `/api/v1/envanter/parts/` endpoint'ine `POST` isteği gönderir.
    *   İstek body'si şunları içermelidir: `serial_number`, `part_type` (ID), `aircraft_model_compatibility` (ID).
    *   Backend, isteği yapan kullanıcının takımını ve parça tipini kontrol eder, başarılı olursa parçayı oluşturur (`status='STOKTA'`, `produced_by_team` set edilir).

4.  **Uçak Monte Etme (Montaj Takımı Üyesi):**
    *   Kullanıcı, frontend'deki "Yeni Uçak Monte Et" formunu kullanır.
    *   Bu form, `/api/v1/montaj/assembled-aircrafts/` endpoint'ine `POST` isteği gönderir.
    *   İstek body'si şunları içermelidir: `tail_number`, `aircraft_model` (ID), `wing` (Part ID), `fuselage` (Part ID), `tail` (Part ID), `avionics` (Part ID).
    *   Backend (`AssembledAircraftSerializer.validate`), parçaların doğru tipte, seçilen uçak modeliyle uyumlu ve stokta olup olmadığını kontrol eder. Başarılı olursa uçak monte edilir ve kullanılan parçaların durumu `KULLANILDI` yapılır.

5.  **Parçayı Geri Dönüşüme Gönderme (Üreten Takım Üyesi):**
    *   Frontend'deki parça listesinde ilgili parçanın "Geri Dönüştür" butonuna tıklanır.
    *   Bu, `/api/v1/envanter/parts/{id}/recycle/` endpoint'ine `POST` isteği gönderir.
    *   Backend, parçanın durumunu `GERI_DONUSUMDE` olarak günceller.

6.  **Admin İşlemleri:**
    *   Adminler, frontend'deki "Admin Paneli" altındaki sayfalardan (Kullanıcı Yönetimi, Takım Yönetimi, Parça Tipi Yönetimi, Uçak Modeli Yönetimi) veya Django Admin panelinden (`/admin/`) ilgili verileri yönetebilirler (listeleme, detay görme; oluşturma/düzenleme/silme işlemleri data migration ile kısıtlanmış olabilir).

## 7. Testler ve Kod Kapsamı

Proje, birim ve entegrasyon testlerini içerir. Testleri çalıştırmak ve kod kapsamı raporu almak için "Kurulum" bölümündeki komutlara bakınız. Hedeflenen kod kapsamı %95 üzeridir.

## 8. Güvenlik Notları

*   Tüm hassas API endpoint'leri token tabanlı kimlik doğrulama ve rol bazlı yetkilendirme ile korunmaktadır.
*   Login ve register endpoint'leri için hız sınırlama (throttling) uygulanmıştır.
*   Canlı ortamda HTTPS kullanılmalı, `DEBUG=False` olmalı ve `SECRET_KEY` güvenli tutulmalıdır.

## 9. Gelecekteki Geliştirmeler

*   Monte edilmiş bir uçağın parçalarının değiştirilebilmesi için daha gelişmiş bir `update` işlevi.
*   Daha detaylı kullanıcı rolleri ve izinleri.
*   Stok hareketleri için loglama.
*   Raporlama arayüzleri.
*   Bildirim sistemi (örn: kritik parça stoğu azaldığında).

---
