from django.db import models

from apps.core.models import TimeStampedModel
from apps.envanter.models import PartType


class Team(TimeStampedModel):
    """
    Üretim ve montaj takımlarını tanımlar.
    """

    TEAM_TYPE_CHOICES = [
        ('KANAT', 'Kanat Takımı'),
        ('GOVDE', 'Gövde Takımı'),
        ('KUYRUK', 'Kuyruk Takımı'),
        ('AVIYONIK', 'Aviyonik Takımı'),
        ('MONTAJ', 'Montaj Takımı'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        choices=TEAM_TYPE_CHOICES, # Her takım tipinden 1er tane olabilir
        verbose_name="Takım Adı"
    )

    # Hangi parça tipinden sorumlu
    responsible_part_type = models.OneToOneField(
        PartType,
        on_delete=models.SET_NULL,
        null=True,  # Montaj takımları için veya bir PartType silinirse
        blank=True,  # Admin panelinde ve formlarda boş bırakılabilir (Montaj takımı için)
        related_name='responsible_team',
        verbose_name="Sorumlu Olduğu Parça Tipi"
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = "Takım"
        verbose_name_plural = "Takımlar"
        ordering = ['name']

    def can_produce_part_type(self, part_type_instance):
        """Bir takımın belirli bir parça tipini üretip üretemeyeceğini kontrol eder."""
        if not part_type_instance:
            return False
        if self.name == 'MONTAJ': # Montaj takımı parça üretemez
            return False
        if not self.responsible_part_type:
            return False
        return self.responsible_part_type == part_type_instance