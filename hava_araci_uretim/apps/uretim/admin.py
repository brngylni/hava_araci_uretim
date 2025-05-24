from django.contrib import admin

from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'responsible_part_type', 'created_at')
    list_filter = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ['responsible_part_type']