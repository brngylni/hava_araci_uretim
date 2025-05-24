from rest_framework import serializers

from apps.core.serializers import TimeStampedSerializer  # Import et
from .models import PartType, AircraftModel, Part


class PartTypeSerializer(TimeStampedSerializer):
    class Meta:
        model = PartType
        fields = ['id', 'name', 'get_name_display', 'created_at', 'updated_at']
        read_only_fields = ['get_name_display', 'id']

class AircraftModelSerializer(TimeStampedSerializer):
    class Meta:
        model = AircraftModel
        fields = ['id', 'name', 'get_name_display', 'created_at', 'updated_at']
        read_only_fields = ['get_name_display', 'id']

class PartSerializer(TimeStampedSerializer):

    # Okunabilir isim alanları
    part_type_name = serializers.CharField(source='part_type.get_name_display', read_only=True)
    aircraft_model_compatibility_name = serializers.CharField(source='aircraft_model_compatibility.get_name_display', read_only=True)
    produced_by_team_name = serializers.CharField(source='produced_by_team.get_name_display', read_only=True, allow_null=True)
    used_in_aircraft_tail_number = serializers.CharField(source='used_in_aircraft.tail_number', read_only=True, allow_null=True) # Uçak kuyruk no null olabileceği için doğru.
    aircraft_model_compatibility = serializers.PrimaryKeyRelatedField(queryset=AircraftModel.objects.all(),
                                                                      allow_null=True, required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Part
        fields = [
            'id', 'serial_number', 'status',
            'part_type', 'part_type_name',
            'aircraft_model_compatibility', 'aircraft_model_compatibility_name',
            'produced_by_team', 'produced_by_team_name',
            'used_in_aircraft', 'used_in_aircraft_tail_number', 'status_display',
            'created_at', 'updated_at'
        ]

        # İş akışıyla değişen salt okunur alanlar
        read_only_fields = [
            'id',
            'status',
            'produced_by_team',
            'used_in_aircraft',
            'part_type_name',
            'aircraft_model_compatibility_name',
            'produced_by_team_name',
            'used_in_aircraft_tail_number'
        ]


class PartMiniSerializer(serializers.ModelSerializer):

    part_type_name = serializers.CharField(source='part_type.get_name_display', read_only=True)
    aircraft_model_compatibility_name = serializers.CharField(source='aircraft_model_compatibility.get_name_display', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)  # status'ün okunabilir hali

    class Meta:
        model = Part
        fields = [
            'id',
            'serial_number',
            'part_type_name',
            'aircraft_model_compatibility_name',
            'status',
            'status_display'
        ]
        read_only_fields = fields  # Tüm alanları salt okunur yapar
