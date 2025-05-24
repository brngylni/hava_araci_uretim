from rest_framework import serializers

from apps.core.serializers import TimeStampedSerializer
from apps.envanter.models import PartType
from .models import Team


class TeamNestedSerializer(serializers.ModelSerializer):
    """
    Diğer serializer'lar içinde Takım bilgisini daha az detayla göstermek için kullanılır.
    Örneğin, bir UserProfile yanıtında kullanıcının takımının sadece ID'sini ve adını göstermek için.
    """

    class Meta:
        model = Team

        fields = ['id', 'get_name_display']
        read_only_fields = fields


class TeamSerializer(TimeStampedSerializer):  # TimeStampedSerializer'dan miras alıyor, güzel.
    """
    Team modeli için tam serileştirme ve validasyon sağlar.
    Takım oluşturma ve güncelleme işlemlerinde kullanılır.
    """

    # Salt okunur alan :
    responsible_part_type_name = serializers.CharField(
        source='responsible_part_type.get_name_display',
        read_only=True,
        allow_null=True
    )

    # Yazılabilir ilişkili alan:
    responsible_part_type = serializers.PrimaryKeyRelatedField(
        queryset=PartType.objects.all(),
        allow_null=True,  # Montaj takımı
        required=False  # Montaj Takımı
    )

    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'get_name_display',
            'responsible_part_type',
            'responsible_part_type_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id',
            'get_name_display',
            'responsible_part_type_name'
        ]


    def validate(self, data):
        """
        Takım adı (tipi) ve sorumlu olduğu parça tipi arasındaki mantıksal tutarlılığı kontrol eder.
        - Montaj takımı bir parça tipinden sorumlu olamaz.
        - Üretim takımları bir parça tipinden sorumlu olmalıdır.
        - Üretim takımının adı (tipi) ile sorumlu olduğu parça tipinin adı eşleşmelidir.
        """

        current_name = data.get('name', getattr(self.instance, 'name', None))
        current_responsible_part_type = data.get('responsible_part_type',
                                                 getattr(self.instance, 'responsible_part_type', None))


        if current_name == 'MONTAJ' and current_responsible_part_type is not None:
            raise serializers.ValidationError({
                "responsible_part_type": "Montaj takımının sorumlu olduğu bir parça tipi olamaz."
            })
        elif current_name != 'MONTAJ' and current_responsible_part_type is None:

            team_display_name = dict(Team.TEAM_TYPE_CHOICES).get(current_name, current_name)
            raise serializers.ValidationError({
                "responsible_part_type": f"{team_display_name} için sorumlu parça tipi belirtilmelidir."
            })
        elif current_name != 'MONTAJ' and current_responsible_part_type is not None:
            # current_name (örn: KANAT) ile current_responsible_part_type.name (örn: KANAT) eşleşmeli.
            if current_name != current_responsible_part_type.name:
                team_display_name = dict(Team.TEAM_TYPE_CHOICES).get(current_name, current_name)
                raise serializers.ValidationError({
                    "responsible_part_type": f"{team_display_name} sadece kendi tipindeki parçalardan sorumlu olabilir. "
                                             f"Beklenen parça tipi: {current_name}, Atanan: {current_responsible_part_type.name}."
                })
        return data
