import factory

from apps.envanter.models import PartType, AircraftModel, Part


class PartTypeFactory(factory.django.DjangoModelFactory):
    """PartType objeleri için fabrika."""
    class Meta:
        model = PartType
        django_get_or_create = ('name',)

    name = factory.Iterator([choice[0] for choice in PartType.PART_TYPE_CHOICES])


class AircraftModelFactory(factory.django.DjangoModelFactory):
    """AircraftModel objeleri için fabrika."""
    class Meta:
        model = AircraftModel
        django_get_or_create = ('name',)

    name = factory.Iterator([choice[0] for choice in AircraftModel.AIRCRAFT_MODEL_CHOICES])



class PartFactory(factory.django.DjangoModelFactory):
    """Part objeleri için fabrika."""

    class Meta:
        model = Part

    part_type = factory.SubFactory(PartTypeFactory)
    serial_number = factory.Sequence(lambda n: f"SN-PART-M2M-{n:05d}")
    aircraft_model_compatibility = factory.SubFactory(AircraftModelFactory) # Geri eklendi
    status = Part.STATUS_CHOICES[0][0] # Varsayılan olarak STOKTA

    @factory.lazy_attribute
    def produced_by_team(self):
        """
        Parçanın tipine uygun bir üretim takımı atar.
        Eğer o tipte bir takım yoksa oluşturur.
        """

        from apps.uretim.models import Team
        team_instance, created = Team.objects.get_or_create(name=self.part_type.name)
        if created:
            if not team_instance.responsible_part_type:
                 team_instance.responsible_part_type = self.part_type # part_type_obj yerine
                 team_instance.save()
        return team_instance
