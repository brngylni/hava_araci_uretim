from django.db import models

from apps.core.models import TimeStampedModel


class PartType(TimeStampedModel):
    """
    Parça tiplerini tanımlar (Kanat, Gövde, Kuyruk, Aviyonik).
    """

    # DB için büyük harf
    PART_TYPE_CHOICES = [
        ('KANAT', 'Kanat'),
        ('GOVDE', 'Gövde'),
        ('KUYRUK', 'Kuyruk'),
        ('AVIYONIK', 'Aviyonik'),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=PART_TYPE_CHOICES,
        verbose_name="Parça Tipi Adı"
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = "Parça Tipi"
        verbose_name_plural = "Parça Tipleri"
        ordering = ['name']


class AircraftModel(TimeStampedModel):
    """
    Uçak modellerini tanımlar (TB2, TB3, AKINCI, KIZILELMA).
    """

    AIRCRAFT_MODEL_CHOICES = [
        ('TB2', 'TB2'),
        ('TB3', 'TB3'),
        ('AKINCI', 'AKINCI'),
        ('KIZILELMA', 'KIZILELMA'),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=AIRCRAFT_MODEL_CHOICES,
        verbose_name="Uçak Modeli Adı"
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = "Uçak Modeli"
        verbose_name_plural = "Uçak Modelleri"
        ordering = ['name']


class Part(TimeStampedModel):
    """
    Üretilen her bir spesifik parçayı temsil eder.
    """

    STATUS_CHOICES = [
        ('STOKTA', 'Stokta'),
        ('KULLANILDI', 'Kullanıldı'),
        ('GERI_DONUSUMDE', 'Geri Dönüşümde'),
    ]

    # Parça tipi
    part_type = models.ForeignKey(
        PartType,
        on_delete=models.PROTECT,  # Parça varsa tip silmeyi engelle
        verbose_name="Parça Tipi"
    )

    # Bu parça HANGİ UÇAK MODELİ İÇİN üretildi
    aircraft_model_compatibility = models.ForeignKey(
        AircraftModel,
        on_delete=models.PROTECT,
        related_name='compatible_parts',
        verbose_name="Uyumlu Uçak Modeli"
    )

    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Seri Numarası"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='STOKTA',
        verbose_name="Durum",
        db_index=True # Sık sık duruma göre filtreleneceği için indexleme performansı arttıracaktır.
    )

    # Parçayı üreten takım
    produced_by_team = models.ForeignKey(
        'uretim.Team', # Döngüsel içe aktarmayı engellemek için
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Testler vs.
        related_name='produced_parts',
        verbose_name="Üreten Takım",
        db_index=True # Sık sık takıma göre filtreleneceği için indexleme performansı arttıracaktır.
    )

    # Kullanıldığı araçlar
    used_in_aircraft = models.ForeignKey(
        'montaj.AssembledAircraft', # Döngüsel içe aktarmayı engellemek için
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Parça ilk başta hiçbir uçağa bağlı değildir.
        related_name='containing_assembly',
        verbose_name="Kullanıldığı Uçak",
        db_index=True # Sık sık uçağa göre filtreleneceği için indexleme performansı arttıracaktır.
    )

    def __str__(self):
        # __str__ metodunu eski haline getirin
        compatibility_display = self.aircraft_model_compatibility.get_name_display() if self.aircraft_model_compatibility else "Uyumsuz/Bilinmiyor"
        return f"{self.part_type.get_name_display()} ({compatibility_display}) - SN: {self.serial_number} [{self.get_status_display()}]"

    class Meta:
        verbose_name = "Parça"
        verbose_name_plural = "Parçalar"
