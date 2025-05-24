from rest_framework import serializers
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.throttling import ScopedRateThrottle
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    UserProfileSerializer
)
from django.contrib.auth.models import User
from rest_framework import viewsets, \
    permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import UserProfile
from .serializers import UserSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from django_filters.rest_framework import DjangoFilterBackend


@extend_schema(
    tags=["Kullanıcılar - User Yönetimi (Admin)"],
    description=(
            "Sistemdeki Django User objelerini listeler ve detaylarını görüntüler. "
            "Bu endpoint'ler öncelikli olarak admin yetkisine sahip kullanıcılar için tasarlanmıştır.\n"
            "Giriş yapmış kullanıcılar kendi temel bilgilerine (profili dahil) `/me/` alt endpoint'inden erişebilir.\n"
            "Bu ViewSet, DataTables server-side processing'i destekler."
    )
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Kullanıcıları listelemek ve detaylarını görmek için salt okunur bir ViewSet.
    `/list` ve `/retrieve` işlemleri sadece admin kullanıcılar tarafından erişilebilir.
    `/me` action'ı ise kimliği doğrulanmış herhangi bir kullanıcının kendi bilgilerini almasını sağlar.
    DataTables server-side işlemleri için `pagination_class` ve `filter_backends` ayarlanmıştır.
    """
    queryset = User.objects.select_related(
        'profile',
        'profile__team'
    ).prefetch_related(
        'groups',
        'user_permissions'
    ).all().order_by('username')

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    # DataTables için ayarlar
    pagination_class = DatatablesPageNumberPagination
    filter_backends = [DatatablesFilterBackend, DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = {
        'username': ['exact', 'icontains'],
        'email': ['exact', 'icontains'],
        'first_name': ['icontains'],
        'last_name': ['icontains'],
        'is_active': ['exact'],
        'is_staff': ['exact'],
        'profile__team': ['exact']
    }
    search_fields = [  # SearchFilter için
        'username',
        'email',
        'first_name',
        'last_name',
        'profile__team__name'  # Takım adına göre arama (eğer Team.name string ise)
    ]
    ordering_fields = [  # OrderingFilter için
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'date_joined',
        'profile__team__name'
    ]
    ordering = ['username']

    @extend_schema(
        summary="Tüm Kullanıcıları Listele (Admin)",
        description="Sistemdeki tüm kullanıcıların (profilleri ve takımları dahil) sayfalanmış bir listesini döndürür. "
                    "Sadece admin yetkisine sahip kullanıcılar erişebilir. DataTables ile uyumludur.",
        parameters=[  # Örnek DjangoFilterBackend parametreleri
            OpenApiParameter(name='username__icontains', description='Kullanıcı adında geçen ifade.',
                             type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='email__icontains', description='E-posta adresinde geçen ifade.',
                             type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='is_active', description='Aktiflik durumuna göre filtrele (true/false).',
                             type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='profile__team', description='Kullanıcının ait olduğu takımın IDsi ile filtrele.',
                             type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
        ],
        responses={  # DataTables yanıtı için
            200: inline_serializer(
                name='UserListDatatablesResponse',
                fields={
                    'draw': serializers.IntegerField(),
                    'recordsTotal': serializers.IntegerField(),
                    'recordsFiltered': serializers.IntegerField(),
                    'data': UserSerializer(many=True)  # UserSerializer listesi
                }
            ),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz).")
        }
    )
    def list(self, request, *args, **kwargs):
        """Kullanıcıların listesini döndürür."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Kullanıcının Detayını Getir (Admin)",
        description="Verilen ID'ye sahip kullanıcının detaylarını (profili ve takımı dahil) döndürür. "
                    "Sadece admin yetkisine sahip kullanıcılar erişebilir.",
        parameters=[
            OpenApiParameter(name='id', description='Kullanıcının unique IDsi.', required=True, type=OpenApiTypes.INT,
                             location=OpenApiParameter.PATH)
        ],
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz)."),
            404: OpenApiResponse(description="Belirtilen ID ile kullanıcı bulunamadı.")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Belirli bir kullanıcının detaylarını döndürür."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Giriş Yapmış Kullanıcının Bilgilerini Getir",
        description="Oturum açmış olan kullanıcının kendi detaylı kullanıcı ve profil bilgilerini döndürür. "
                    "Bu endpoint için kullanıcının sadece kimliğinin doğrulanmış olması yeterlidir.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli (Token eksik veya geçersiz).")
        }
    )
    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])  # İzin burada override ediliyor
    def me(self, request):
        """Giriş yapmış kullanıcının kendi bilgilerini döndürür."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@extend_schema(
    tags=["Kullanıcılar - Kimlik Doğrulama"],
    summary="Yeni Kullanıcı Kaydı",
    description="Yeni bir kullanıcı hesabı oluşturur. Kullanıcı adı, e-posta ve şifre zorunludur. "
                "İsteğe bağlı olarak bir `team_id` gönderilerek kullanıcı bir takıma atanabilir. "
                "Başarılı kayıt sonrası oluşturulan kullanıcı bilgileri (şifre hariç) döndürülür.",
    request=UserRegistrationSerializer,
    responses={
        201: UserSerializer,  # Başarılı kayıtta UserSerializer ile kullanıcı bilgisi döner
        400: OpenApiResponse(
            description="Geçersiz veri veya validasyon hatası (örn: şifreler uyuşmuyor, geçersiz team_id, eksik alanlar).")
    }
)
class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'registration_attempts'


@extend_schema(
    tags=["Kullanıcılar - Kimlik Doğrulama"],
    summary="Kullanıcı Girişi",
    description="Kullanıcı adı ve şifre ile kimlik doğrulaması yapar. Başarılı girişte, kullanıcıya ait "
                "bir API token'ı ve temel kullanıcı bilgileri döndürülür. "
                "Bu token, yetki gerektiren diğer API endpoint'lerine yapılan isteklerde "
                "`Authorization: Token <token_değeri>` başlığında kullanılmalıdır.",
    request=LoginSerializer,  # İstek body'si username ve password içermeli
    responses={
        200: inline_serializer(  # Başarılı giriş yanıtı için anlık serializer
            name='UserLoginSuccessResponse',
            fields={
                'token': serializers.CharField(),
                'user': UserSerializer()  # UserSerializer'ı burada nested olarak kullanabiliriz
            }
        ),
        400: OpenApiResponse(description="Kullanıcı hesabı aktif değil."),
        401: OpenApiResponse(description="Geçersiz kullanıcı adı veya şifre.")
    }
)
class UserLoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login_attempts'

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "Geçersiz kullanıcı adı veya şifre."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({"error": "Geçersiz kullanıcı adı veya şifre."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"error": "Kullanıcı hesabı aktif değil."}, status=status.HTTP_400_BAD_REQUEST)
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user, context={'request': request}).data
        return Response({
            "token": token.key,
            "user": user_data
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Kullanıcılar - User Profili Yönetimi"],
    description="Kullanıcı profillerini yönetir. Adminler tüm profillere erişebilirken, "
                "normal kullanıcılar sadece kendi profillerini `/my_profile/` üzerinden yönetebilir."
)
class UserProfileViewSet(viewsets.ModelViewSet):
    """
    Kullanıcı profillerini yönetmek için bir ViewSet.
    Adminler tüm profilleri listeleyebilir ve güncelleyebilir.
    Giriş yapmış kullanıcılar `/my_profile/` endpoint'i üzerinden kendi profillerini
    görüntüleyebilir ve güncelleyebilir (sadece takım ataması gibi).
    """
    queryset = UserProfile.objects.select_related('user', 'team').all().order_by('user__username')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]  # Varsayılan izin

    @extend_schema(
        summary="Tüm Kullanıcı Profillerini Listele (Admin)",
        description="Sistemdeki tüm kullanıcı profillerinin sayfalanmış bir listesini döndürür. Sadece adminler erişebilir.",
        responses={200: UserProfileSerializer(many=True),
                   401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
                   403: OpenApiResponse(description="Yetkiniz yok.")}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Kullanıcı Profilinin Detayını Getir (Admin)",
        description="Verilen ID'ye sahip kullanıcı profilinin detaylarını döndürür. Sadece adminler erişebilir.",
        parameters=[OpenApiParameter(name='id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH,
                                     description="Profil ID'si")],
        responses={200: UserProfileSerializer, 401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
                   403: OpenApiResponse(description="Yetkiniz yok."),
                   404: OpenApiResponse(description="Profil bulunamadı.")}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Kullanıcı Profilini Güncelle (Admin)",
        description="Belirli bir kullanıcının profilini günceller (örn: takımını değiştirir). Sadece adminler erişebilir.",
        request=UserProfileSerializer,
        parameters=[OpenApiParameter(name='id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH,
                                     description="Profil ID'si")],
        responses={200: UserProfileSerializer, 400: OpenApiResponse(description="Geçersiz veri."),
                   401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
                   403: OpenApiResponse(description="Yetkiniz yok."),
                   404: OpenApiResponse(description="Profil bulunamadı.")}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Kullanıcı Profilini Kısmen Güncelle (Admin)",
        description="Belirli bir kullanıcının profilinin gönderilen alanlarını günceller. Sadece adminler erişebilir.",
        request=UserProfileSerializer,
        parameters=[OpenApiParameter(name='id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH,
                                     description="Profil ID'si")],
        responses={200: UserProfileSerializer, 400: OpenApiResponse(description="Geçersiz veri."),
                   401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
                   403: OpenApiResponse(description="Yetkiniz yok."),
                   404: OpenApiResponse(description="Profil bulunamadı.")}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


    @extend_schema(exclude=True)  # Dökümantasyondan çıkar
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(exclude=True)  # Dökümantasyondan çıkar
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Kendi Profil Bilgilerimi Getir/Güncelle",
        description="Giriş yapmış kullanıcının kendi profil bilgilerini (örn: takımını) görüntülemesini ve güncellemesini sağlar.",
        request=UserProfileSerializer,  # Güncelleme için body şeması
        responses={
            200: UserProfileSerializer,  # Başarılı GET veya PUT/PATCH yanıtı
            400: OpenApiResponse(description="Geçersiz veri (güncelleme sırasında)."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            404: OpenApiResponse(description="Kullanıcı profili bulunamadı.")
        }
    )
    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def my_profile(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({"error": "Kullanıcı profili bulunamadı. Lütfen bir yönetici ile iletişime geçin."},
                            status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(profile, data=request.data, partial=(request.method == 'PATCH'))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
