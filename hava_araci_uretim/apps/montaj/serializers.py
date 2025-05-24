from rest_framework import serializers

from apps.core.serializers import TimeStampedSerializer
from apps.envanter.models import AircraftModel, Part, PartType
from apps.envanter.serializers import AircraftModelSerializer, PartMiniSerializer
from apps.uretim.serializers import TeamNestedSerializer
from .models import AssembledAircraft


class AssembledAircraftSerializer(TimeStampedSerializer):  # TimeStampedSerializer'dan miras alıyor, güzel.
    """
    Monte edilmiş bir AssembledAircraft objesinin serileştirilmesi ve validasyonu için kullanılır.
    Bu serializer, yeni bir uçak montajı (create) ve mevcut bir uçağın
    detaylarını gösterme/güncelleme (retrieve, update, partial_update) işlemlerini yönetir.
    """

    # ---- Salt Okunur Detay Alanları (Read-only Detail Fields) ----

    aircraft_model_details = AircraftModelSerializer(source='aircraft_model', read_only=True)
    assembled_by_team_details = TeamNestedSerializer(source='assembled_by_team', read_only=True)

    wing_details = PartMiniSerializer(source='wing', read_only=True)
    fuselage_details = PartMiniSerializer(source='fuselage', read_only=True)
    tail_details = PartMiniSerializer(source='tail', read_only=True)
    avionics_details = PartMiniSerializer(source='avionics', read_only=True)

    # ---- Yazılabilir İlişkili Alanlar (Writable Relational Fields) ----
    aircraft_model = serializers.PrimaryKeyRelatedField(queryset=AircraftModel.objects.all())

    wing = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(status='STOKTA'))
    fuselage = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(status='STOKTA'))
    tail = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(status='STOKTA'))
    avionics = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(status='STOKTA'))

    class Meta:
        model = AssembledAircraft
        fields = [
            'id', 'tail_number',
            'aircraft_model', 'aircraft_model_details',
            'wing', 'wing_details',
            'fuselage', 'fuselage_details',
            'tail', 'tail_details',
            'avionics', 'avionics_details',
            'assembled_by_team', 'assembled_by_team_details',
            'assembly_date',  # Modelde auto_now_add=True
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id',
            'assembly_date',  # Modelde auto_now_add=True
            'assembled_by_team',  # View perform_create metodunda set ediliyor
            'aircraft_model_details',
            'assembled_by_team_details',
            'wing_details', 'fuselage_details',
            'tail_details', 'avionics_details',
        ]

    def validate(self, data):
        """
        Gelen verinin iş kurallarına göre validasyonunu yapar.
        - Yeni uçak oluşturulurken tüm parçaların zorunlu olması.
        - Parçaların benzersiz olması (aynı parça birden fazla rolde kullanılamaz).
        - Seçilen parçaların doğru tipte olması.
        - Seçilen parçaların hedeflenen uçak modeliyle uyumlu olması (ManyToManyField üzerinden).
        - Seçilen parçaların (eğer yeni atanıyorsa) stokta olması.
        """

        is_creating = self.instance is None
        aircraft_model_instance = data.get('aircraft_model', getattr(self.instance, 'aircraft_model', None))

        if not aircraft_model_instance:
            raise serializers.ValidationError({"aircraft_model": "Uçak modeli belirtilmelidir."})

        part_field_definitions = {
            'wing': {'expected_type_code': 'KANAT'}, 'fuselage': {'expected_type_code': 'GOVDE'},
            'tail': {'expected_type_code': 'KUYRUK'}, 'avionics': {'expected_type_code': 'AVIYONIK'}
        }
        errors = {}

        # Ön belleğe almak db yükünü azaltabilir.
        # Constructora taşınabilir
        _cached_part_types = {pt.name: pt for pt in PartType.objects.filter(
            name__in=[d['expected_type_code'] for d in part_field_definitions.values()])}

        if is_creating:
            for field_name, defs in part_field_definitions.items():
                if field_name not in data or not data[field_name]:
                    expected_pt_obj = _cached_part_types.get(defs['expected_type_code'])
                    pt_display_name = expected_pt_obj.get_name_display() if expected_pt_obj else defs[
                        'expected_type_code']
                    errors[field_name] = [f"{pt_display_name} parçası seçilmelidir."]
            if errors:
                raise serializers.ValidationError(errors)

        parts_being_validated = {}
        for field_name_loop in part_field_definitions.keys():
            if field_name_loop in data:
                if data[field_name_loop] is not None:
                    parts_being_validated[field_name_loop] = data[field_name_loop]
                elif not is_creating and not self.partial and data[field_name_loop] is None:
                    expected_pt_obj = _cached_part_types.get(
                        part_field_definitions[field_name_loop]['expected_type_code'])
                    pt_display_name = expected_pt_obj.get_name_display() if expected_pt_obj else \
                    part_field_definitions[field_name_loop]['expected_type_code']
                    errors[field_name_loop] = [f"{pt_display_name} parçası boş bırakılamaz (PUT)."]

        if not parts_being_validated and not is_creating and self.partial:
            if errors: raise serializers.ValidationError(errors)
            return data

        part_ids = [p.id for p in parts_being_validated.values() if p]
        if len(part_ids) > 1 and len(part_ids) != len(set(part_ids)):
            errors.setdefault("non_field_errors", []).append("Aynı parça birden fazla rolde kullanılamaz.")

        for field_name, part_instance in parts_being_validated.items():
            if not part_instance: continue

            expected_type_code = part_field_definitions[field_name]['expected_type_code']
            field_specific_errors = errors.get(field_name, [])

            expected_part_type_obj = _cached_part_types.get(expected_type_code)
            if not expected_part_type_obj:  # Bu durum kritik bir sistem hatasıdır
                errors.setdefault('configuration_error', []).append(
                    f"Sistemde beklenen '{expected_type_code}' parça tipi bulunamadı.")
                continue

            expected_part_type_display_name = expected_part_type_obj.get_name_display()

            if part_instance.part_type != expected_part_type_obj:
                field_specific_errors.append(
                    f"Seçilen {part_instance.serial_number} parçası, beklenen {expected_part_type_display_name} tipiyle uyuşmuyor."
                )
            elif part_instance.aircraft_model_compatibility != aircraft_model_instance:
                field_specific_errors.append(
                    f"{part_instance.serial_number} parçası, hedeflenen uçak modeli ({aircraft_model_instance.get_name_display()}) ile uyumlu değil."
                )

            is_newly_assigned_part = True
            if not is_creating and self.instance:
                if getattr(self.instance, field_name) == part_instance:
                    is_newly_assigned_part = False

            if is_newly_assigned_part and part_instance.status != 'STOKTA':
                field_specific_errors.append(f"{part_instance.serial_number} parçası stokta değil, kullanılamaz.")

            if field_specific_errors:
                current_errors_for_field = errors.get(field_name, [])
                for e in field_specific_errors:
                    if e not in current_errors_for_field:
                        current_errors_for_field.append(e)
                if current_errors_for_field:
                    errors[field_name] = current_errors_for_field

        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Eğer montajdan sonra parça değişimi kısıtlanacaksa parçalar update içerisinde read_only yapılabilir
        instance.tail_number = validated_data.get('tail_number', instance.tail_number)
        part_fields = ['wing', 'fuselage', 'tail', 'avionics']
        changed_parts_info = []

        for field in part_fields:
            old_part = getattr(instance, field)
            if field in validated_data:  # Eğer bu parça alanı update isteğinde gönderilmişse
                new_part = validated_data[field]
                if old_part != new_part:
                    setattr(instance, field, new_part)
                    changed_parts_info.append({'field': field, 'old': old_part, 'new': new_part})

        # Önce uçağın kendisini (tail_number ve yeni parça referanslarıyla) kaydet
        instance.save()  # Bu, modelin save() metodunu çağırır, ama is_new=False olur.
        # Dolayısıyla modelin save() metodu parça durumlarını GÜNCELLEMEZ.

        # Şimdi değişen parçaların durumlarını yönet
        for change in changed_parts_info:
            new_part = change['new']
            old_part = change['old']

            if new_part:  # Yeni bir parça atanmışsa
                if new_part.status == 'STOKTA':  # Sadece stoktaysa güncelle, değilse buraya gelemez
                    new_part.status = 'KULLANILDI'
                    new_part.used_in_aircraft = instance
                    new_part.save(update_fields=['status', 'used_in_aircraft', 'updated_at'])

            if old_part:  # Eğer eski bir parça varsa ve yeni bir parçayla değiştirilmişse
                old_part.status = 'STOKTA'
                old_part.used_in_aircraft = None
                old_part.save(update_fields=['status', 'used_in_aircraft', 'updated_at'])
        return instance


class MissingPartsQuerySerializer(serializers.Serializer):
    """
    check_missing_parts action'ı için query parametrelerini valide eder.
    """
    aircraft_model_name = serializers.ChoiceField(choices=AircraftModel.AIRCRAFT_MODEL_CHOICES)
