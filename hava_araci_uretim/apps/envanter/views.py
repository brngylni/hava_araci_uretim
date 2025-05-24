from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.pagination import DatatablesPageNumberPagination

from apps.core.permissions import IsProductionTeamAndResponsibleForPartType, CanRecyclePart
from .models import PartType, AircraftModel, Part
from .serializers import PartTypeSerializer, AircraftModelSerializer, PartSerializer


@extend_schema(
    tags=["Envanter - Parça Tipleri"], # Swagger UI'da gruplama için etiket
    description="Sistemde tanımlı olan parça tiplerini (Kanat, Gövde vb.) listeler ve detaylarını gösterir."
)
class PartTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Parça tiplerini (Kanat, Gövde vb.) listelemek ve detaylarını görmek için salt okunur ViewSet.
    """

    queryset = PartType.objects.all().order_by('name')
    serializer_class = PartTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Tüm Parça Tiplerini Listele",
        description="Sistemdeki tüm parça tiplerinin sayfalanmış bir listesini döndürür.",
        responses={
            200: PartTypeSerializer(many=True),  # Başarılı yanıtın şeması
            401: OpenApiResponse(
                description="Kimlik doğrulaması gerekli (Authentication credentials were not provided).")
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Parça Tipinin Detayını Getir",
        description="Verilen ID'ye sahip parça tipinin detaylarını döndürür.",
        parameters=[
            OpenApiParameter(name='id', description='Parça tipinin unique IDsi.', required=True, type=OpenApiTypes.INT,
                             location=OpenApiParameter.PATH)
        ],
        responses={
            200: PartTypeSerializer(),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            404: OpenApiResponse(description="Belirtilen ID ile parça tipi bulunamadı.")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=["Envanter - Uçak Modelleri"],
    description="Sistemde tanımlı olan uçak modellerini (TB2, AKINCI vb.) listeler ve detaylarını gösterir."
)
class AircraftModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Uçak modellerini (TB2, AKINCI vb.) listelemek ve detaylarını görmek için salt okunur ViewSet.
    """

    queryset = AircraftModel.objects.all().order_by('name')
    serializer_class = AircraftModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Tüm Uçak Modellerini Listele",
        description="Sistemdeki tüm uçak modellerinin sayfalanmış bir listesini döndürür.",
        responses={200: AircraftModelSerializer(many=True),
                   401: OpenApiResponse(description="Kimlik doğrulaması gerekli.")}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Uçak Modelinin Detayını Getir",
        description="Verilen ID'ye sahip uçak modelinin detaylarını döndürür.",
        parameters=[
            OpenApiParameter(name='id', description='Uçak modelinin unique IDsi.', required=True, type=OpenApiTypes.INT,
                             location=OpenApiParameter.PATH)
        ],
        responses={200: AircraftModelSerializer(), 401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
                   404: OpenApiResponse(description="Belirtilen ID ile uçak modeli bulunamadı.")}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=["Envanter - Parça Tipleri (Admin)"],  # Etiket güncellendi
    description="Sistemde tanımlı olan parça tiplerini (Kanat, Gövde vb.) yönetir. CRUD işlemleri sadece admin yetkisine sahip kullanıcılar tarafından gerçekleştirilebilir."
)
class PartTypeViewSet(viewsets.ModelViewSet):  # ReadOnlyModelViewSet'ten ModelViewSet'e değiştirildi
    """
    Parça tiplerini yönetmek için ViewSet.
    Listeleme, detay görme, oluşturma, güncelleme ve silme işlemlerini destekler.
    Tüm işlemler (list/retrieve hariç) için admin yetkisi (`IsAdminUser`) gerekir.
    Listeleme ve detay görme için kimliği doğrulanmış olmak (`IsAuthenticated`) yeterlidir.
    """
    queryset = PartType.objects.all().order_by('name')
    serializer_class = PartTypeSerializer

    # permission_classes = [permissions.IsAuthenticated] # ESKİ

    def get_permissions(self):
        """Aksiyona göre izinleri ayarlar."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        # list, retrieve için varsayılan (IsAuthenticated veya settings'ten gelen)
        return [permissions.IsAuthenticated()]

        # @extend_schema tanımları create, update, destroy için eklenebilir.

    # list ve retrieve için olanlar zaten vardı, güncellenebilir.

    @extend_schema(summary="Yeni Parça Tipi Oluştur (Admin)", request=PartTypeSerializer,
                   responses={201: PartTypeSerializer, 400: OpenApiResponse(description="Geçersiz veri."),
                              403: OpenApiResponse(description="Yetkiniz yok.")})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Tüm Parça Tiplerini Listele", responses={200: PartTypeSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Belirli Bir Parça Tipinin Detayını Getir",
                   responses={200: PartTypeSerializer, 404: OpenApiResponse(description="Bulunamadı.")})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Parça Tipini Güncelle (Admin)", request=PartTypeSerializer,
                   responses={200: PartTypeSerializer, 400: OpenApiResponse(description="Geçersiz veri."),
                              403: OpenApiResponse(description="Yetkiniz yok."),
                              404: OpenApiResponse(description="Bulunamadı.")})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Parça Tipini Kısmen Güncelle (Admin)", request=PartTypeSerializer,
                   responses={200: PartTypeSerializer, 400: OpenApiResponse(description="Geçersiz veri."),
                              403: OpenApiResponse(description="Yetkiniz yok."),
                              404: OpenApiResponse(description="Bulunamadı.")})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Parça Tipini Sil (Admin)",
                   responses={204: OpenApiResponse(description="Başarıyla silindi."),
                              403: OpenApiResponse(description="Yetkiniz yok."),
                              404: OpenApiResponse(description="Bulunamadı."), 409: OpenApiResponse(
                           description="Bu parça tipi kullanıldığı için silinemiyor (PROTECT).")})
    def destroy(self, request, *args, **kwargs):
        # PartType.parts ilişkisi on_delete=PROTECT olduğu için, eğer bu tipte parçalar varsa
        # silme işlemi IntegrityError (ProtectedError) verecektir.
        # DRF bunu 400 veya 409 Conflict'e çevirebilir veya 500 verebilir.
        # Bunu handle etmek için perform_destroy'u override edebiliriz.
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:  # django.db.models.deletion.ProtectedError
            return Response(
                {
                    "error": f"Bu parça tipi, mevcut parçalar tarafından kullanıldığı için silinemiyor. (Detay: {str(e)})"},
                status=status.HTTP_409_CONFLICT
            )

@extend_schema(
    tags=["Envanter - Uçak Modelleri"],
    description="Sistemde tanımlı olan uçak modellerini (TB2, AKINCI vb.) listeler ve detaylarını gösterir."
)
class AircraftModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Uçak modellerini (TB2, AKINCI vb.) listelemek ve detaylarını görmek için salt okunur ViewSet.
    Tüm işlemler için kullanıcının kimliğinin doğrulanmış olması (`IsAuthenticated`) gerekir.
    """
    queryset = AircraftModel.objects.all().order_by('name')
    serializer_class = AircraftModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Tüm Uçak Modellerini Listele",
        description="Sistemdeki tüm uçak modellerinin sayfalanmış bir listesini döndürür.",
        responses={200: AircraftModelSerializer(many=True),
                   401: OpenApiResponse(description="Kimlik doğrulaması gerekli.")}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Uçak Modelinin Detayını Getir",
        description="Verilen ID'ye sahip uçak modelinin detaylarını döndürür.",
        parameters=[
            OpenApiParameter(name='id', description='Uçak modelinin unique IDsi.', required=True, type=OpenApiTypes.INT,
                             location=OpenApiParameter.PATH)
        ],
        responses={200: AircraftModelSerializer, 401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
                   404: OpenApiResponse(description="Belirtilen ID ile uçak modeli bulunamadı.")}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=["Envanter - Parçalar"],
    description="Sistemdeki üretilmiş bireysel parçaları yönetir. Parça oluşturma, listeleme, detay görme, "
                "güncelleme (kısıtlı), geri dönüşüme gönderme ve silme (sadece admin) işlemlerini içerir. "
                "Bu endpoint, jQuery DataTables server-side processing ile uyumludur."  # DataTables notu eklendi
)
class PartViewSet(viewsets.ModelViewSet):
    """
    Üretilmiş parçaları yönetmek için ViewSet (CRUD işlemleri).
    İzinler ve bazı iş mantıkları `get_permissions()` ve `perform_create()` gibi
    metotlarla yönetilir. DataTables server-side processing'i destekler.
    """
    queryset = Part.objects.select_related(
        'part_type',
        'produced_by_team',
        'used_in_aircraft',
        'aircraft_model_compatibility'  # ForeignKey için select_related
    ).order_by('-created_at')

    serializer_class = PartSerializer

    # DataTables için güncellemeler
    pagination_class = DatatablesPageNumberPagination
    filter_backends = [DatatablesFilterBackend, DjangoFilterBackend]

    filterset_fields = {
        'part_type': ['exact'],
        'status': ['exact'],
        'produced_by_team': ['exact'],
        'aircraft_model_compatibility': ['exact'],  # ForeignKey için filtreleme
        'serial_number': ['exact', 'icontains'],
    }

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsProductionTeamAndResponsibleForPartType()]
        elif self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsProductionTeamAndResponsibleForPartType()]
        elif self.action == 'destroy':
            return [permissions.IsAdminUser()]
        elif self.action == 'recycle':
            return [permissions.IsAuthenticated(), CanRecyclePart()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        summary="Yeni Parça Üret (Oluştur)",
        description="Yeni bir parça oluşturur. Sadece sorumlu üretim takımı tarafından çağrılabilir. "
                    "Parçanın tipi, istek yapan takımın sorumlu olduğu parça tipiyle eşleşmelidir. "
                    "Oluşturulan parça otomatik olarak 'STOKTA' durumunda ve üreten takıma bağlı olur. "
                    "`aircraft_model_compatibility` alanı (ID olarak) zorunludur.",  # Ek bilgi
        request=PartSerializer,
        responses={
            201: PartSerializer,
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok.")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user_team = self.request.user.profile.team
        part_type_requested = serializer.validated_data.get('part_type')

        if not user_team or user_team.name == 'MONTAJ' or user_team.responsible_part_type != part_type_requested:
            raise PermissionDenied(
                detail="Takımınız bu parça tipini üretemez veya bir üretim takımı değil."
            )
        serializer.save(
            produced_by_team=user_team,
            status='STOKTA'
        )

    @extend_schema(
        summary="Tüm Parçaları Listele",
        description="Sistemdeki tüm parçaların sayfalanmış bir listesini döndürür. "
                    "Standart DRF filtreleme parametrelerinin yanı sıra (aşağıda listelenmiştir), "
                    "jQuery DataTables server-side processing için gerekli olan "
                    "`draw`, `start`, `length`, `search[value]`, `order[][column/dir]` gibi "
                    "parametreleri de destekler. Yanıt formatı DataTables uyumludur.",
        parameters=[
            OpenApiParameter(name='part_type', description='Parça tipine göre filtrele (ID).', type=OpenApiTypes.INT,
                             location=OpenApiParameter.QUERY),
            OpenApiParameter(name='status', description='Duruma göre filtrele (örn: STOKTA, KULLANILDI).',
                             type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                             enum=[s[0] for s in Part.STATUS_CHOICES]),  # Enum eklendi
            OpenApiParameter(name='produced_by_team', description='Üreten takıma göre filtrele (ID).',
                             type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='aircraft_model_compatibility',
                             description='Uyumlu uçak modeline göre filtrele (ID).', type=OpenApiTypes.INT,
                             location=OpenApiParameter.QUERY),  # Güncellendi
            OpenApiParameter(name='serial_number', description='Seri numarasına göre tam eşleşme ile filtrele.',
                             type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='serial_number__icontains',
                             description='Seri numarasında geçen ifadeye göre (büyük/küçük harf duyarsız) filtrele.',
                             type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            # DataTables'a özgü parametreler (draw, start, length vb.) genellikle otomatik algılanır veya
            # DataTables kullanıcıları tarafından bilinir, buraya eklemek şart değil.
        ],
        responses={  # DataTables yanıtı için inline_serializer kullanmak daha doğru olur
            200: inline_serializer(
                name='PartListDatatablesResponse',
                fields={
                    'draw': serializers.IntegerField(),
                    'recordsTotal': serializers.IntegerField(),
                    'recordsFiltered': serializers.IntegerField(),
                    'data': PartSerializer(many=True)
                }
            ),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli.")
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Parçanın Detayını Getir",
        description="Verilen ID'ye sahip parçanın detaylarını döndürür.",
        parameters=[
            OpenApiParameter(name='id', description='Parçanın unique IDsi.', required=True, type=OpenApiTypes.INT,
                             location=OpenApiParameter.PATH)
        ],
        responses={200: PartSerializer, 401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
                   404: OpenApiResponse(description="Parça bulunamadı.")}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Parçayı Güncelle (Kısmi)",
        description="Bir parçanın belirli alanlarını günceller. Parça tipi veya temel uyumluluk "
                    "gibi özellikler genellikle değiştirilemez (veya serializer'da read_only olmalıdır). "
                    "İzinler, üreten takım ve sorumlu parça tipi ile kısıtlıdır.",
        request=PartSerializer,
        responses={
            200: PartSerializer,
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok."),
            404: OpenApiResponse(description="Parça bulunamadı.")
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Parçayı Güncelle (Tam)",
        description="Bir parçanın tüm yazılabilir alanlarını günceller. `partial_update` ile benzer kısıtlamalara ve validasyonlara tabidir.",
        request=PartSerializer,
        responses={
            200: PartSerializer,
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok."),
            404: OpenApiResponse(description="Parça bulunamadı.")
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Parçayı Geri Dönüşüme Gönder",
        description="Belirli bir parçanın durumunu 'GERI_DONUSUMDE' olarak ayarlar. "
                    "Sadece parçayı üreten takım tarafından çağrılabilir. "
                    "Kullanımda olan veya zaten geri dönüşümde olan parçalar için işlem yapılmaz.",
        request=None,
        responses={
            200: inline_serializer(
                name='RecycleSuccessResponse',
                fields={'message': serializers.CharField()}
            ),
            400: OpenApiResponse(
                description="Parça kullanımda olduğu için geri dönüşüme gönderilemiyor veya zaten geri dönüşümde."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu parçayı geri dönüşüme gönderme yetkiniz yok."),
            404: OpenApiResponse(description="Parça bulunamadı.")
        }
    )
    @action(detail=True, methods=['post'], url_path='recycle')
    def recycle(self, request, pk=None):
        part = self.get_object()
        if part.status == 'KULLANILDI':
            return Response(
                {"error": "Kullanımda olan bir parça doğrudan geri dönüşüme gönderilemez. Önce uçaktan sökülmelidir."},
                status=status.HTTP_400_BAD_REQUEST)
        if part.status == 'GERI_DONUSUMDE':
            return Response({"message": "Parça zaten geri dönüşümde."}, status=status.HTTP_200_OK)  # Veya 400
        part.status = 'GERI_DONUSUMDE'
        part.used_in_aircraft = None
        part.save(update_fields=['status', 'used_in_aircraft', 'updated_at'])
        return Response({"message": f"'{part.serial_number}' seri numaralı parça başarıyla geri dönüşüme gönderildi."},
                        status=status.HTTP_200_OK)

    @extend_schema(
        summary="Parçayı Sil (Sadece Admin)",
        description="Belirli bir parçayı veritabanından kalıcı olarak siler. Bu işlem sadece admin yetkisine "
                    "sahip kullanıcılar tarafından yapılabilir. Normal kullanıcılar 'recycle' endpoint'ini kullanmalıdır.",
        request=None,
        responses={
            204: OpenApiResponse(description="Parça başarıyla silindi (İçerik Yok)."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Bu işlemi yapma yetkiniz yok (Admin değilsiniz)."),
            404: OpenApiResponse(description="Parça bulunamadı.")
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.delete()