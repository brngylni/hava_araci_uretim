# apps/montaj/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# İlgili ViewSet'i import ediyoruz:
from .views import AssembledAircraftViewSet

router = DefaultRouter()

# AssembledAircraftViewSet'i router'a kaydediyoruz.
# URL: /api/v1/montaj/assembled-aircrafts/
# AssembledAircraftViewSet içindeki 'check_missing_parts' action'ı (detail=False) için URL:
# /api/v1/montaj/assembled-aircrafts/check_missing_parts/ otomatik olarak oluşturulacaktır.
router.register(r'assembled-aircrafts', AssembledAircraftViewSet, basename='assembledaircraft')

urlpatterns = [
    # Router tarafından oluşturulan tüm URL'leri dahil et.
    path('', include(router.urls)),
]