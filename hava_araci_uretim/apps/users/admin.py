from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil Bilgileri'
    fk_name = 'user'
    autocomplete_fields = ['team']


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_team')
    list_select_related = ('profile', 'profile__team')

    def get_team(self, instance):
        if hasattr(instance, 'profile') and instance.profile.team:
            return instance.profile.team.name
        return None
    get_team.short_description = 'Takımı'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

