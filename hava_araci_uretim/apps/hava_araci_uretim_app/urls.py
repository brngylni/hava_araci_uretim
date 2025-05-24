# hava_araci_uretim/hava_araci_uretim/urls.py

from django.contrib import admin
from django.urls import path, include
# API dökümantasyonu (Swagger/OpenAPI) için drf-spectacular view'lerini import ediyoruz:
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# API endpoint'lerimiz için ortak bir ön ek tanımlıyoruz.
# Bu, API versiyonlaması veya genel bir gruplama için kullanışlıdır.
API_PREFIX = 'api/v1/' 

urlpatterns = [
    # Django admin paneli için URL:
    path('admin/', admin.site.urls),

    # Şimdi uygulama seviyesindeki urls.py dosyalarını API_PREFIX altına dahil ediyoruz:
    # apps.envanter uygulamasının URL'lerini /api/v1/envanter/ altına bağlıyoruz.
    path(f'{API_PREFIX}envanter/', include('apps.envanter.urls')),
    # apps.uretim uygulamasının URL'lerini /api/v1/uretim/ altına bağlıyoruz.
    path(f'{API_PREFIX}uretim/', include('apps.uretim.urls')),
    # apps.users uygulamasının URL'lerini /api/v1/users/ altına bağlıyoruz.
    path(f'{API_PREFIX}users/', include('apps.users.urls')),
    # apps.montaj uygulamasının URL'lerini /api/v1/montaj/ altına bağlıyoruz.
    path(f'{API_PREFIX}montaj/', include('apps.montaj.urls')),

    # API Schema ve Dökümantasyon URL'leri (drf-spectacular):
    # API schema dosyasını (OpenAPI formatında) sunan endpoint:
    path(f'{API_PREFIX}schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI arayüzünü sunan endpoint:
    # url_name='schema' parametresi, Swagger UI'ın schema dosyasını nereden alacağını belirtir.
    path(f'{API_PREFIX}schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ReDoc arayüzünü sunan endpoint:
    path(f'{API_PREFIX}schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]