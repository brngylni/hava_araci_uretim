from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    """
    Django User modeline ek personel bilgilerini ekler.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE, # User silinirse profili de sil
        related_name='profile',
        verbose_name="Kullanıcı"
    )

    # Personel takımı
    team = models.ForeignKey(
        'uretim.Team',  # Döngüsel içe aktarımı engellemek için
        on_delete=models.SET_NULL,  # Takım silinirse personel takımsız kalır
        null=True,
        blank=True,
        related_name='members',
        verbose_name="Takımı",
        db_index=True # Sık sık takıma göre filtreleneceği için indexleme performansı arttıracaktır.
    )

    def __str__(self):
        team_name_display = str(self.team) if self.team else 'Takımsız'
        return f"{self.user.username} Profili ({team_name_display})"

    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"
        ordering = ['user__username']


# User oluşunca profil de oluşsun sinyali
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save() # Silinebilir (opsiyonel)