from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework_datatables.filters import DatatablesFilterBackend

from .models import Team
from .serializers import TeamSerializer


@extend_schema(
    tags=["Üretim - Takımlar"], # Swagger UI'da gruplama için etiket
    description="Sistemdeki üretim ve montaj takımlarını yönetir. Tüm CRUD işlemleri sadece admin yetkisine sahip kullanıcılar tarafından gerçekleştirilebilir."
)
class TeamViewSet(viewsets.ModelViewSet):
    """
    Üretim ve Montaj Takımlarını yönetmek için ViewSet.
    Bu ViewSet, takımların listelenmesi, detaylarının görülmesi, oluşturulması (admin),
    güncellenmesi (admin) ve silinmesi (admin) işlemlerini destekler.
    Takım tipi ('name' alanı) ve sorumlu olduğu parça tipi ('responsible_part_type')
    arasındaki tutarlılık, TeamSerializer içinde valide edilir.
    """
    queryset = Team.objects.select_related(
        'responsible_part_type'
    ).all().order_by('name') # Alfabetik sıralama
    filter_backends = [DatatablesFilterBackend, DjangoFilterBackend, SearchFilter, OrderingFilter]

    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAdminUser] # Sadece adminler erişebilir

    filterset_fields = {
        'name': ['exact'],  # Takım tipine göre filtre
        'responsible_part_type': ['exact'],  # Sorumlu parça tipine göre filtre
    }
    search_fields = ['name']  # Takım adına/tipine göre arama
    ordering_fields = ['name', 'created_at']  # Sıralanabilir alanlar
    ordering = ['name']  # Varsayılan sıralama

    @extend_schema(
        summary="Yeni Takım Oluştur (Admin)",
        description="Yeni bir üretim veya montaj takımı oluşturur. "
                    "Takım adı (`name`) sistemde tanımlı tiplerden biri olmalıdır (KANAT, GOVDE, MONTAJ vb.). "
                    "Eğer bir üretim takımı (`name` != 'MONTAJ') oluşturuluyorsa, "
                    "`responsible_part_type` (ID olarak) gönderilmeli ve `name` ile eşleşmelidir. "
                    "Montaj takımı için `responsible_part_type` gönderilmemeli veya null olmalıdır.",
        request=TeamSerializer, # İstek body'si TeamSerializer'a uygun olmalı
        responses={
            201: TeamSerializer, # Başarılı oluşturmada takım bilgileri döner
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası (örn: isim-parça tipi uyuşmazlığı)."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli (Token eksik veya geçersiz)."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz).")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Tüm Takımları Listele (Admin)",
        description="Sistemdeki tüm takımların sayfalanmış bir listesini döndürür.",
        responses={
            200: TeamSerializer(many=True), # Başarılı yanıtta takım listesi
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz).")
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Takımın Detayını Getir (Admin)",
        description="Verilen ID'ye sahip takımın detaylarını döndürür.",
        parameters=[
            OpenApiParameter(name='id', description='Takımın unique IDsi.', required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH)
        ],
        responses={
            200: TeamSerializer,
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz)."),
            404: OpenApiResponse(description="Belirtilen ID ile takım bulunamadı.")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Takımı Güncelle (Kısmi - Admin)",
        description="Bir takımın belirli alanlarını günceller. Takım adı ('name') genellikle değiştirilemez. "
                    "Eğer 'responsible_part_type' güncelleniyorsa, takımın 'name' alanı ile uyumlu olmalıdır.",
        request=TeamSerializer, # İstek body'si TeamSerializer'a uygun olmalı
        responses={
            200: TeamSerializer,
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz)."),
            404: OpenApiResponse(description="Takım bulunamadı.")
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Takımı Güncelle (Tam - Admin)",
        description="Bir takımın tüm yazılabilir alanlarını günceller. `partial_update` ile benzer validasyon kurallarına tabidir.",
        request=TeamSerializer,
        responses={
            200: TeamSerializer,
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz)."),
            404: OpenApiResponse(description="Takım bulunamadı.")
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Takımı Sil (Admin)",
        description="Belirli bir takımı veritabanından kalıcı olarak siler. "
                    "Eğer bu takım UserProfile veya Part modellerinde `on_delete=models.SET_NULL` "
                    "ile referans alınıyorsa, ilgili objelerdeki takım alanı null olur. "
                    "Eğer `on_delete=models.PROTECT` ile referans alınıyorsa ve bağlı objeler varsa silme işlemi başarısız olur.",
        parameters=[
            OpenApiParameter(name='id', description='Silinecek takımın unique IDsi.', required=True, type=OpenApiTypes.INT, location=OpenApiParameter.PATH)
        ],
        request=None, # İstek body'si yok
        responses={
            204: OpenApiResponse(description="Takım başarıyla silindi (İçerik Yok)."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz)."),
            404: OpenApiResponse(description="Takım bulunamadı."),
            # Eğer PROTECT nedeniyle silinemezse 400 veya 409 gibi bir hata dönebilir, bu ayrıca belgelenebilir.
            409: OpenApiResponse(description="Takım, başka objeler tarafından kullanıldığı için silinemiyor (PROTECT).") 
        }
    )
    def destroy(self, request, *args, **kwargs):

        return super().destroy(request, *args, **kwargs)