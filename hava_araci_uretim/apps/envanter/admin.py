from django.contrib import admin

from .models import Part
from .models import PartType, AircraftModel


@admin.register(PartType)
class PartTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)

@admin.register(AircraftModel)
class AircraftModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number',
        'part_type',
        'aircraft_model_compatibility',
        'status',
        'produced_by_team',
        'used_in_aircraft',
        'created_at'
    )
    list_filter = (
        'status',
        'part_type',
        'aircraft_model_compatibility',
        'produced_by_team'
    )
    search_fields = (
        'serial_number',
        'used_in_aircraft__tail_number',
        'part_type__name',
        'aircraft_model_compatibility__name'
    )
    autocomplete_fields = [
        'part_type',
        'aircraft_model_compatibility',
        'produced_by_team',
        'used_in_aircraft'
    ]

    list_select_related = (
        'part_type',
        'aircraft_model_compatibility',
        'produced_by_team',
        'used_in_aircraft'
    )
