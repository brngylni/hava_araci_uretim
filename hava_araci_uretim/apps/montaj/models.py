from django.db import models

from apps.core.models import TimeStampedModel
from apps.envanter.models import AircraftModel, Part, PartType
from apps.uretim.models import Team


class AssembledAircraft(TimeStampedModel):
    """
    Monte edilmiş bir uçağı temsil eder.
    """

    aircraft_model = models.ForeignKey(
        AircraftModel,
        on_delete=models.PROTECT, # Montajı yapılmış bir uçak varken modeli silinmemeli
        related_name='assembled_aircrafts',
        verbose_name="Uçak Modeli"
    )

    tail_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Kuyruk Numarası"
    )

    assembly_date = models.DateField(
        auto_now_add=True, # Montajın tamamlandığı tarih
        verbose_name="Montaj Tarihi"
    )


    assembled_by_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'name': 'MONTAJ'},
        verbose_name="Montajı Yapan Takım"
    )

    wing = models.OneToOneField(Part, on_delete=models.PROTECT, related_name='used_as_wing_in', verbose_name="Kanat Parçası")
    fuselage = models.OneToOneField(Part, on_delete=models.PROTECT, related_name='used_as_fuselage_in', verbose_name="Gövde Parçası")
    tail = models.OneToOneField(Part, on_delete=models.PROTECT, related_name='used_as_tail_in', verbose_name="Kuyruk Parçası")
    avionics = models.OneToOneField(Part, on_delete=models.PROTECT, related_name='used_as_avionics_in', verbose_name="Aviyonik Parçası")

    def __str__(self):
        return f"{self.aircraft_model} - {self.tail_number} (Monte Edildi: {self.assembly_date})"

    def clean(self):
        from django.core.exceptions import ValidationError

        # Temel PartType'ları çek
        try:
            kanat_type_obj = PartType.objects.get(name='KANAT')
            govde_type_obj = PartType.objects.get(name='GOVDE')
            kuyruk_type_obj = PartType.objects.get(name='KUYRUK')
            aviyonik_type_obj = PartType.objects.get(name='AVIYONIK')
        except PartType.DoesNotExist as e:
            raise ValidationError(f"Temel parça tipleri bulunamadı: {e}. Lütfen veritabanını kontrol edin.") from e

        # Parça alanlarını ve beklenen tiplerini tanımla
        part_definitions = {
            'wing': {'expected_part_type': kanat_type_obj, 'verbose_name': self._meta.get_field('wing').verbose_name},
            'fuselage': {'expected_part_type': govde_type_obj,
                         'verbose_name': self._meta.get_field('fuselage').verbose_name},
            'tail': {'expected_part_type': kuyruk_type_obj, 'verbose_name': self._meta.get_field('tail').verbose_name},
            'avionics': {'expected_part_type': aviyonik_type_obj,
                         'verbose_name': self._meta.get_field('avionics').verbose_name},
        }

        validation_errors = {}
        assigned_parts_instances = []  # Benzersizlik kontrolü için

        for field_name, defs in part_definitions.items():
            part_instance = None
            field_specific_errors = []

            # Parçanın instance'ını güvenli bir şekilde almayı dene
            try:
                related_id_field_name = f"{field_name}_id"
                if hasattr(self, related_id_field_name) and getattr(self, related_id_field_name) is not None:
                    part_instance = getattr(self, field_name)  # Bu, obje varsa onu getirir

            except Part.DoesNotExist:
                part_instance = None  # İlişkili obje yoksa

            if not part_instance:

                field_specific_errors.append(f"{defs['verbose_name']} atanmalıdır.")
            else:
                assigned_parts_instances.append(part_instance)

                # Parça tipi doğru mu?
                if part_instance.part_type != defs['expected_part_type']:
                    field_specific_errors.append(
                        f"{defs['verbose_name']} için seçilen parça ({part_instance.serial_number}) yanlış tipte. "
                        f"Beklenen tip: {defs['expected_part_type'].get_name_display()}."
                    )

                # Parça bu uçak modeliyle uyumlu mu?
                if not self.aircraft_model:
                    validation_errors.setdefault('aircraft_model', []).append("Uçağın modeli belirtilmemiş.")
                elif part_instance.aircraft_model_compatibility != self.aircraft_model:
                    field_specific_errors.append(
                        f"{defs['verbose_name']} için seçilen parça ({part_instance.serial_number}) bu uçak modeli ({self.aircraft_model}) ile uyumlu değil."
                    )

                # Parça stokta mı? (Yeni montaj için)
                if self.pk is None and part_instance.status != 'STOKTA':
                    field_specific_errors.append(
                        f"{defs['verbose_name']} için seçilen parça ({part_instance.serial_number}) stokta değil (Durumu: {part_instance.get_status_display()})."
                    )

            if field_specific_errors:
                validation_errors[field_name] = field_specific_errors

        # Kullanılan tüm parçaların ID'lerinin benzersiz olduğundan emin olalım
        if assigned_parts_instances:  # Eğer en az bir parça atanmışsa
            part_ids = [p.id for p in assigned_parts_instances]
            if len(part_ids) != len(set(part_ids)):
                validation_errors.setdefault('__all__', []).append(
                    "Bir uçak için aynı parça birden fazla rolde kullanılamaz.")

        if validation_errors:
            raise ValidationError(validation_errors)

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # Model seviyesinde validasyon için eklenebilir
        #if is_new:
        #    self.full_clean()

        super().save(*args, **kwargs)  # DB

        if is_new:  # Yeni bir uçak monte edildiğinde parçaları güncelle
            parts_to_update = [self.wing, self.fuselage, self.tail, self.avionics]
            for part in parts_to_update:
                if part:  # Ekstra güvenlik
                    part.status = 'KULLANILDI'
                    part.used_in_aircraft = self  # Uçağa bağla
                    part.save(update_fields=['status', 'used_in_aircraft',
                                             'updated_at'])  # Sadece belirli alanları güncelle

    class Meta:
        verbose_name = "Monte Edilmiş Uçak"
        verbose_name_plural = "Monte Edilmiş Uçaklar"
        ordering = ['-assembly_date']  # En son monte edilenler üstte