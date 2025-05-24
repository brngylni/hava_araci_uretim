# apps/uretim/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# İlgili ViewSet'i import ediyoruz:
from .views import TeamViewSet

router = DefaultRouter()

# TeamViewSet'i router'a kaydediyoruz.
# URL: /api/v1/uretim/teams/
router.register(r'teams', TeamViewSet, basename='team')

urlpatterns = [
    # Router tarafından oluşturulan tüm URL'leri dahil et.
    path('', include(router.urls)),
]