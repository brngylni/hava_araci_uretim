from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.permissions import IsAssemblyTeam
from apps.envanter.models import Part, AircraftModel, PartType
from .models import AssembledAircraft
from .serializers import AssembledAircraftSerializer, MissingPartsQuerySerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework.filters import SearchFilter, OrderingFilter


@extend_schema(
    tags=["Montaj - Monte Edilmiş Uçaklar"],
    description=(
            "Monte edilmiş uçakların yönetimi için ana endpoint.\n"
            "- **Oluşturma (POST):** Yeni bir uçak monte eder. Sadece Montaj Takımı erişebilir.\n"
            "- **Listeleme (GET):** Tüm monte edilmiş uçakları listeler. Kimliği doğrulanmış tüm kullanıcılar erişebilir.\n"
            "- **Detay (GET /id/):** Belirli bir uçağın detaylarını gösterir. Kimliği doğrulanmış tüm kullanıcılar erişebilir.\n"
            "- **Güncelleme (PUT/PATCH /id/):** Bir uçağın bilgilerini günceller (örn: kuyruk numarası). Sadece Montaj Takımı erişebilir.\n"
            "  Not: Uçağın parçalarını değiştirmek karmaşık bir işlemdir ve mevcut durumda sınırlı desteklenebilir.\n"
            "- **Silme (DELETE /id/):** Bir uçağı siler ve kullanılan parçaları stoğa döndürür. Sadece Montaj Takımı erişebilir.\n"
            "- **/check_missing_parts/ (GET):** Belirli bir uçak modeli için eksik parçaları kontrol eder."
    )
)
class AssembledAircraftViewSet(viewsets.ModelViewSet):
    """
    Monte edilmiş hava araçlarının oluşturulması, listelenmesi, güncellenmesi
    ve silinmesi gibi CRUD operasyonlarını yönetir. Ayrıca, belirli bir uçak
    modeli için envanterdeki eksik parçaları kontrol etmek amacıyla özel bir
    aksiyon (`check_missing_parts`) sunar.

    Yetkilendirme:
    - `create`, `update`, `partial_update`, `destroy` işlemleri sadece `IsAssemblyTeam` iznine sahip
      kullanıcılara (Montaj Takımı üyelerine) açıktır.
    - `list`, `retrieve`, `check_missing_parts` işlemleri kimliği doğrulanmış (`IsAuthenticated`)
      tüm kullanıcılara açıktır.

    İş Mantığı:
    - Yeni bir uçak oluşturulduğunda (`perform_create` ve `AssembledAircraft.save()`):
        - Montajı yapan takım, isteği yapan kullanıcının takımı olarak atanır.
        - Kullanılan parçaların (`wing`, `fuselage`, `tail`, `avionics`) durumu 'KULLANILDI' olarak
          güncellenir ve bu uçağa bağlanır.
    - Bir uçak silindiğinde (`perform_destroy`):
        - Uçakta kullanılan parçaların durumu 'STOKTA' olarak güncellenir ve uçakla olan
          bağlantıları kaldırılır. Bu işlem atomik bir transaction içinde yapılır.
    """
    queryset = AssembledAircraft.objects.select_related(
        'aircraft_model',
        'assembled_by_team',
        'wing', 'fuselage', 'tail', 'avionics',
        'wing__part_type',
        'fuselage__part_type',
        'tail__part_type',
        'avionics__part_type',
        'wing__aircraft_model_compatibility',  # ForeignKey olduğunu varsayıyoruz
        'fuselage__aircraft_model_compatibility',
        'tail__aircraft_model_compatibility',
        'avionics__aircraft_model_compatibility',
    ).order_by('-assembly_date', '-created_at')

    serializer_class = AssembledAircraftSerializer
    pagination_class = DatatablesPageNumberPagination  # DataTables için
    filter_backends = [DatatablesFilterBackend, DjangoFilterBackend, SearchFilter, OrderingFilter]  # DataTables ve standart filtreleme
    filterset_fields = {
        'aircraft_model': ['exact'],
        'assembled_by_team': ['exact'],
        'tail_number': ['icontains'],
        'assembly_date': ['exact', 'gte', 'lte', 'range']
    }

    def get_permissions(self):
        """İşleme göre uygun izinleri dinamik olarak döndürür."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAssemblyTeam()]
        elif self.action == 'check_missing_parts':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        summary="Yeni Uçak Monte Et (Montaj Takımı)",
        description=(
                "Verilen parçaları ve uçak modeli bilgilerini kullanarak yeni bir hava aracı monte eder. "
                "Bu işlem sadece 'Montaj Takımı' rolündeki kullanıcılar tarafından gerçekleştirilebilir.\n"
                "İstek body'sinde `aircraft_model` (ID), `tail_number` ve her bir ana parça (`wing`, `fuselage`, `tail`, `avionics`) için "
                "geçerli, stokta olan ve belirtilen uçak modeliyle uyumlu `Part` ID'leri gönderilmelidir.\n"
                "Başarılı montaj sonrası, kullanılan parçaların durumu otomatik olarak 'KULLANILDI' olarak güncellenir "
                "ve `assembled_by_team` alanı isteği yapan kullanıcının takımı olarak ayarlanır."
        ),
        request=AssembledAircraftSerializer,
        responses={
            201: AssembledAircraftSerializer,
            400: OpenApiResponse(
                description="Geçersiz veri: Eksik veya yanlış parça bilgisi, parça uyumsuzluğu, stokta olmayan parça veya diğer validasyon hataları."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(
                description="Yetki hatası: Bu işlemi yapma yetkiniz yok (örn: Montaj Takımı üyesi değilsiniz).")
        }
    )
    def create(self, request, *args, **kwargs):
        """Yeni bir AssembledAircraft instance'ı oluşturur."""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Yeni bir AssembledAircraft oluşturulurken, `assembled_by_team` alanını
        otomatik olarak isteği yapan kullanıcının takımı ile doldurur.
        """
        user_team = self.request.user.profile.team
        serializer.save(assembled_by_team=user_team)

    @extend_schema(
        summary="Tüm Monte Edilmiş Uçakları Listele",
        description=(
                "Sistemde kayıtlı tüm monte edilmiş uçakların sayfalanmış bir listesini döndürür.\n"
                "Bu endpoint, jQuery DataTables server-side processing ile uyumludur ve DataTables tarafından "
                "gönderilen `draw`, `start`, `length`, `search[value]`, `order[][column/dir]` gibi "
                "parametreleri destekler. Ayrıca, aşağıda listelenen standart filtre parametreleri de kullanılabilir."
        ),
        parameters=[  # filterset_fields için OpenApiParameter tanımları (isteğe bağlı, drf-spectacular algılayabilir)
            OpenApiParameter(name='aircraft_model', description='Uçak modeline göre filtrele (ID).',
                             type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='assembled_by_team', description='Montajı yapan takıma göre filtrele (ID).',
                             type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='tail_number__icontains',
                             description='Kuyruk numarasında geçen ifadeye göre (büyük/küçük harf duyarsız) filtrele.',
                             type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='assembly_date', description='Tam montaj tarihine göre filtrele (YYYY-AA-GG).',
                             type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='assembly_date__gte',
                             description='Belirtilen tarihten itibaren (eşit ve büyük) monte edilmiş uçakları filtrele.',
                             type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
            # ... diğer date filtreleri için de eklenebilir ...
        ],
        responses={
            200: inline_serializer(  # DataTables yanıtı için
                name='AssembledAircraftListDatatablesResponse',
                fields={
                    'draw': serializers.IntegerField(),
                    'recordsTotal': serializers.IntegerField(),
                    'recordsFiltered': serializers.IntegerField(),
                    'data': AssembledAircraftSerializer(many=True)
                }
            ),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli.")
        }
    )
    def list(self, request, *args, **kwargs):
        """Monte edilmiş tüm AssembledAircraft instance'larını listeler."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Belirli Bir Monte Edilmiş Uçağın Detayını Getir",
        description="Verilen ID'ye sahip monte edilmiş uçağın tüm detaylarını döndürür.",
        parameters=[
            OpenApiParameter(name='id', description='Monte edilmiş uçağın unique IDsi.', required=True,
                             type=OpenApiTypes.INT, location=OpenApiParameter.PATH)
        ],
        responses={
            200: AssembledAircraftSerializer,
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            404: OpenApiResponse(description="Belirtilen ID ile monte edilmiş uçak bulunamadı.")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Belirli bir AssembledAircraft instance'ının detaylarını döndürür."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Monte Edilmiş Uçağı Güncelle (Kısmi - Montaj Takımı)",
        description=(
                "Bir monte edilmiş uçağın belirli alanlarını günceller. "
                "Bu işlem sadece 'Montaj Takımı' rolündeki kullanıcılar tarafından gerçekleştirilebilir.\n"
                "Genellikle sadece `tail_number` gibi parça olmayan alanların güncellenmesi beklenir. "
                "Uçağın parçalarının (`wing`, `fuselage` vb.) bu endpoint üzerinden değiştirilmesi, "
                "eski parçaların stoğa döndürülmesi ve yeni parçaların durumunun güncellenmesi gibi "
                "karmaşık iş mantıklarını tetikler (eğer `AssembledAircraftSerializer.update` metodu "
                "bu şekilde implemente edilmişse)."
        ),
        request=AssembledAircraftSerializer,
        responses={
            200: AssembledAircraftSerializer,
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Yetki hatası."),
            404: OpenApiResponse(description="Monte edilmiş uçak bulunamadı.")
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Belirli bir AssembledAircraft instance'ının gönderilen alanlarını günceller."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Monte Edilmiş Uçağı Güncelle (Tam - Montaj Takımı)",
        description=(
                "Bir monte edilmiş uçağın tüm yazılabilir alanlarını günceller. "
                "`partial_update` ile benzer kısıtlamalara ve iş mantıklarına tabidir. "
                "Sadece 'Montaj Takımı' rolündeki kullanıcılar tarafından gerçekleştirilebilir."
        ),
        request=AssembledAircraftSerializer,
        responses={
            200: AssembledAircraftSerializer,
            400: OpenApiResponse(description="Geçersiz veri veya validasyon hatası."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Yetki hatası."),
            404: OpenApiResponse(description="Monte edilmiş uçak bulunamadı.")
        }
    )
    def update(self, request, *args, **kwargs):
        """Bir AssembledAircraft instance'ını tamamen günceller."""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Monte Edilmiş Uçağı Sil (Montaj Takımı)",
        description=(
                "Belirli bir monte edilmiş uçağı veritabanından siler. "
                "Bu işlem sadece 'Montaj Takımı' rolündeki kullanıcılar tarafından gerçekleştirilebilir.\n"
                "Silme işlemi sırasında, uçakta kullanılan ana parçalar (kanat, gövde, kuyruk, aviyonik) "
                "otomatik olarak 'STOKTA' durumuna geri döndürülür ve uçakla olan bağlantıları kaldırılır."
        ),
        parameters=[
            OpenApiParameter(name='id', description='Silinecek monte edilmiş uçağın unique IDsi.', required=True,
                             type=OpenApiTypes.INT, location=OpenApiParameter.PATH)
        ],
        request=None,
        responses={
            204: OpenApiResponse(description="Uçak başarıyla silindi (İçerik Yok)."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            403: OpenApiResponse(description="Yetki hatası."),
            404: OpenApiResponse(description="Monte edilmiş uçak bulunamadı.")
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Bir AssembledAircraft instance'ını siler."""
        return super().destroy(request, *args, **kwargs)

    @transaction.atomic
    def perform_destroy(self, instance):
        """
        Bir AssembledAircraft silinmeden önce, ilişkili parçaları stoğa döndürür.
        Bu işlem atomik bir transaction içinde yapılır.
        """
        parts_to_release = [instance.wing, instance.fuselage, instance.tail, instance.avionics]
        for part in parts_to_release:
            if part:
                part.status = 'STOKTA'
                part.used_in_aircraft = None
                part.save(update_fields=['status', 'used_in_aircraft', 'updated_at'])
        instance.delete()

    @extend_schema(
        summary="Belirli Uçak Modeli İçin Eksik Parçaları Kontrol Et",
        description=(
                "Verilen `aircraft_model_name` query parametresine göre, o uçak modeli için "
                "gerekli olan temel parçaların (Kanat, Gövde, Kuyruk, Aviyonik) envanterdeki "
                "stok durumunu ve eksik parçalar varsa uyarıları döndürür."
        ),
        parameters=[
            OpenApiParameter(
                name='aircraft_model_name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Stok durumu kontrol edilecek uçak modelinin adı.',
                enum=[choice[0] for choice in AircraftModel.AIRCRAFT_MODEL_CHOICES]
            )
        ],
        responses={
            200: inline_serializer(
                name='MissingPartsResponse',  # Yanıt şeması için açıklayıcı bir isim
                fields={
                    'aircraft_model': serializers.CharField(help_text="Kontrol edilen uçak modelinin adı."),
                    'required_parts_check': serializers.DictField(
                        child=serializers.IntegerField(),
                        help_text="Her bir temel parça tipi için stokta bulunan adet."
                    ),
                    'message': serializers.CharField(required=False,
                                                     help_text="Genel durum mesajı (tüm parçalar varsa)."),
                    'warnings': serializers.ListField(
                        child=serializers.CharField(),
                        required=False,
                        help_text="Eksik parçalar veya sistem hataları için uyarı listesi."
                    )
                }
            ),
            400: OpenApiResponse(description="Geçersiz veya eksik 'aircraft_model_name' parametresi."),
            401: OpenApiResponse(description="Kimlik doğrulaması gerekli."),
            404: OpenApiResponse(description="Belirtilen uçak modeli sistemde bulunamadı.")
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def check_missing_parts(self, request):
        """
        Belirli bir uçak modeli için envanterdeki temel parçaların stok durumunu kontrol eder
        ve eksiklikler hakkında bilgi verir.
        """
        query_serializer = MissingPartsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        aircraft_model_name = query_serializer.validated_data['aircraft_model_name']

        try:
            aircraft_model_instance = AircraftModel.objects.get(name=aircraft_model_name)
        except AircraftModel.DoesNotExist:
            return Response({"error": "Belirtilen uçak modeli bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        required_part_type_names = ['KANAT', 'GOVDE', 'KUYRUK', 'AVIYONIK']
        part_types_map = {pt.name: pt for pt in PartType.objects.filter(name__in=required_part_type_names)}

        warnings = []
        available_parts_summary = {}

        for name_code in required_part_type_names:
            pt = part_types_map.get(name_code)
            display_name_for_summary = name_code
            if not pt:
                warnings.append(f"Sistem konfigürasyon hatası: Tanımlı '{name_code}' parça tipi bulunamadı!")
                available_parts_summary[display_name_for_summary] = 0
                continue

            display_name_for_summary = pt.get_name_display()
            count = Part.objects.filter(
                aircraft_model_compatibility=aircraft_model_instance,  # ForeignKey varsayımı
                part_type=pt,
                status='STOKTA'
            ).distinct().count()

            available_parts_summary[display_name_for_summary] = count
            if count == 0:
                warnings.append(
                    f"{aircraft_model_instance.get_name_display()} için {display_name_for_summary} parçası stokta bulunmamaktadır."
                )

        response_data = {
            "aircraft_model": aircraft_model_instance.get_name_display(),
            "required_parts_check": available_parts_summary,
        }

        if warnings:
            response_data["warnings"] = warnings
        else:
            response_data[
                "message"] = f"{aircraft_model_instance.get_name_display()} için tüm temel parçalardan en az birer adet stokta mevcut."

        return Response(response_data, status=status.HTTP_200_OK)