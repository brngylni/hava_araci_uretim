import factory

from apps.envanter.models import PartType
from apps.uretim.models import Team


class TeamFactory(factory.django.DjangoModelFactory):
    """
    Team objeleri için temel fabrika.
    Üretim takımları için varsayılan olarak isimleriyle eşleşen bir PartType'ı
    responsible_part_type olarak atamaya çalışır.
    """

    class Meta:
        model = Team
        django_get_or_create = ('name',)

    name = factory.Iterator([choice[0] for choice in Team.TEAM_TYPE_CHOICES if choice[0] != 'MONTAJ'])

    @factory.post_generation
    def set_responsible_part_type(obj, create, extracted, **kwargs):
        """
        Eğer takım bir üretim takımıysa (adı 'MONTAJ' değilse) ve adı geçerli bir
        PartType adı ile eşleşiyorsa, ilgili PartType'ı bulur/oluşturur ve
        takımın responsible_part_type'ı olarak atar.
        """

        _PART_TYPE_NAMES = [choice[0] for choice in PartType.PART_TYPE_CHOICES]  # Güncel listeyi alalım

        if obj.name != 'MONTAJ' and obj.name in _PART_TYPE_NAMES:
            part_type_instance, _ = PartType.objects.get_or_create(name=obj.name)
            obj.responsible_part_type = part_type_instance

            if create: # Ek Kontrol
                obj.save(update_fields=['responsible_part_type'])  # Sadece bu alanı güncelle.
        elif obj.name == 'MONTAJ':  # Ek kontrol: Montaj takımının responsible_part_type'ı None olmalı.
            if obj.responsible_part_type is not None:
                obj.responsible_part_type = None
                if create:  # veya if obj.pk: (eğer obje zaten DB'de ise)
                    obj.save(update_fields=['responsible_part_type'])


class KanatTeamFactory(TeamFactory):
    """'KANAT' adında bir Team oluşturur ve KANAT PartType'ını sorumlu olarak atar."""
    name = 'KANAT'
    # set_responsible_part_type post_generation metodu KANAT PartType'ını atayacaktır


class GovdeTeamFactory(TeamFactory):
    """'GOVDE' adında bir Team oluşturur ve GOVDE PartType'ını sorumlu olarak atar."""
    name = 'GOVDE'


class KuyrukTeamFactory(TeamFactory):
    """'KUYRUK' adında bir Team oluşturur ve KUYRUK PartType'ını sorumlu olarak atar."""
    name = 'KUYRUK'


class AviyonikTeamFactory(TeamFactory):
    """'AVIYONIK' adında bir Team oluşturur ve AVIYONIK PartType'ını sorumlu olarak atar."""
    name = 'AVIYONIK'


class AssemblyTeamFactory(TeamFactory):
    """'MONTAJ' adında bir Team oluşturur, responsible_part_type'ı None olur."""
    name = 'MONTAJ'