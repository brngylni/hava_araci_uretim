# apps/envanter/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# İlgili ViewSet'leri import ediyoruz:
from .views import PartTypeViewSet, AircraftModelViewSet, PartViewSet

router = DefaultRouter()

# PartTypeViewSet'i router'a kaydediyoruz.
# URL: /api/v1/envanter/part-types/
router.register(r'part-types', PartTypeViewSet, basename='parttype')

# AircraftModelViewSet'i router'a kaydediyoruz.
# URL: /api/v1/envanter/aircraft-models/
router.register(r'aircraft-models', AircraftModelViewSet, basename='aircraftmodel')

# PartViewSet'i router'a kaydediyoruz.
# URL: /api/v1/envanter/parts/
# PartViewSet içindeki 'recycle' action'ı (detail=True) için URL:
# /api/v1/envanter/parts/{id}/recycle/ otomatik olarak oluşturulacaktır.
router.register(r'parts', PartViewSet, basename='part')

urlpatterns = [
    # Router tarafından oluşturulan tüm URL'leri dahil et.
    path('', include(router.urls)),
]