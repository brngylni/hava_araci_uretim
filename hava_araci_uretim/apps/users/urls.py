# apps/users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# İlgili view'leri ve viewset'leri import ediyoruz:
from .views import UserViewSet, UserRegistrationAPIView, UserLoginAPIView, UserProfileViewSet

# DefaultRouter, DRF'in sunduğu bir router sınıfıdır.
# ViewSet'ler için standart URL pattern'lerini (list, create, retrieve, update, destroy)
# ve ViewSet içinde @action ile tanımlanan custom action'lar için URL'leri otomatik olarak oluşturur.
router = DefaultRouter()

# UserViewSet'i router'a kaydediyoruz.
# 'users' -> URL'de kullanılacak ön ek (örn: /api/v1/users/users/)
# UserViewSet -> Kaydedilecek ViewSet sınıfı
# basename='user' -> URL isimlerini oluştururken kullanılacak temel isim.
# Eğer queryset tanımlıysa basename otomatik atanabilir, ama belirtmek iyi bir pratiktir.
router.register(r'users', UserViewSet, basename='user')
# Not: UserViewSet'in permission_classes'ı [permissions.IsAdminUser] olduğu için
# bu endpoint'lere sadece adminler erişebilecek. 'me' action'ı hariç.

# UserProfileViewSet'i router'a kaydediyoruz.
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
# Not: UserProfileViewSet'in permission_classes'ı [permissions.IsAdminUser] olduğu için
# bu endpoint'lere sadece adminler erişebilecek. 'my_profile' action'ı hariç.

# urlpatterns listesi, Django'nun URL yönlendirmesi için kullanacağı pattern'leri içerir.
urlpatterns = [
    # Router tarafından oluşturulan URL'leri urlpatterns'e dahil ediyoruz.
    # Bu, /users/ ve /profiles/ ile başlayan tüm URL'leri (ve custom action'larını) ekler.
    path('', include(router.urls)),

    # UserRegistrationAPIView (generics.CreateAPIView) için özel bir path tanımlıyoruz,
    # çünkü bu bir ViewSet değil, tek bir endpoint'tir.
    path('register/', UserRegistrationAPIView.as_view(), name='user-register'),
    # .as_view() metodu, class-based view'leri Django'nun beklediği callable'a dönüştürür.
    # name='user-register', bu URL'e Django içinde tersine mühendislik (reverse URL lookup)
    # yapmak için bir isim verir (örn: reverse('user-register')).

    # UserLoginAPIView (generics.GenericAPIView) için özel bir path tanımlıyoruz.
    path('login/', UserLoginAPIView.as_view(), name='user-login'),

    # Token bazlı logout için DRF'in doğrudan bir endpoint'i yoktur.
    # Genellikle client tarafında token silinir. Eğer sunucu tarafında token'ı
    # geçersiz kılmak istenirse, özel bir endpoint yazılabilir. Şimdilik eklemiyoruz.

    # UserProfileViewSet içindeki 'my_profile' action'ı için URL:
    # Eğer router.register içinde ViewSet'imiz varsa ve action detail=False ise
    # router otomatik olarak 'profiles/my_profile/' şeklinde bir URL oluşturur.
    # Ancak bazen daha explicit olmak veya farklı bir path kullanmak isteyebiliriz.
    # UserProfileViewSet'teki my_profile action'ı detail=False olduğu için router bunu
    # /profiles/my_profile/ olarak zaten oluşturacaktır.
    # Eğer farklı bir path istenseydi şöyle yapılabilirdi (ama şu an gereksiz):
    # path('profile/me/', UserProfileViewSet.as_view({'get': 'my_profile', 'put': 'my_profile', 'patch': 'my_profile'}), name='my-profile-custom-path'),
]