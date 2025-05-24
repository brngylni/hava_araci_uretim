from django.contrib import admin

from .models import AssembledAircraft


@admin.register(AssembledAircraft)
class AssembledAircraftAdmin(admin.ModelAdmin):
    list_display = (
        'tail_number',
        'aircraft_model',
        'assembly_date',
        'assembled_by_team',
        'wing',
        'fuselage',
        'tail',
        'avionics'
    )

    list_filter = ('aircraft_model', 'assembly_date', 'assembled_by_team')
    search_fields = ('tail_number', 'aircraft_model__name')
    autocomplete_fields = [
        'aircraft_model',
        'assembled_by_team',
        'wing',
        'fuselage',
        'tail',
        'avionics'
    ]
    readonly_fields = ('assembly_date',)
