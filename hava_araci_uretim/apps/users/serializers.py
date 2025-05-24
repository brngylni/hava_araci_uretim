from django.contrib.auth.models import User
from rest_framework import serializers

from apps.core.serializers import TimeStampedSerializer
from apps.uretim.models import Team
from apps.uretim.serializers import TeamNestedSerializer
from .models import UserProfile


class UserProfileSerializer(TimeStampedSerializer):
    """
    UserProfile modeli için serileştirme ve validasyon sağlar.
    Kullanıcının takım bilgisini ve diğer profil detaylarını yönetir.
    """

    # Takım Detayları
    team_details = TeamNestedSerializer(source='team', read_only=True, allow_null=True)


    # Yazılabilir ilişkili alan:
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        allow_null=True, # Takım null olabilir.
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'team',
            'team_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    date_joined = serializers.DateTimeField(read_only=True) # User modelinden
    last_login = serializers.DateTimeField(read_only=True, allow_null=True) # User modelinden

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'date_joined', 'last_login', 'is_staff', 'is_active']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'is_staff', 'is_active']

    def update(self, instance, validated_data):
        profile_data_from_validation = validated_data.pop('profile', None)
        instance = super().update(instance, validated_data)

        if profile_data_from_validation is not None:
            profile_instance = instance.profile

            data_for_profile_serializer = {}
            if 'team' in profile_data_from_validation:
                team_object = profile_data_from_validation['team']
                if team_object is None:
                    data_for_profile_serializer['team'] = None
                elif isinstance(team_object, Team):  # Gelen bir Team instance'ı mı?
                    data_for_profile_serializer['team'] = team_object.pk  # ID'sini al
                else:
                    data_for_profile_serializer['team'] = team_object

            for key, value in profile_data_from_validation.items():
                if key != 'team':
                    data_for_profile_serializer[key] = value

            if not data_for_profile_serializer:
                return instance

            profile_serializer = UserProfileSerializer(
                instance=profile_instance,
                data=data_for_profile_serializer,
                partial=True,
                context=self.context
            )
            if profile_serializer.is_valid(raise_exception=True):
                profile_serializer.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    # ... (önceki haliyle aynı) ...
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    team_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'team_id']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Şifreler eşleşmiyor."})
        team_id = data.get('team_id')
        if team_id and not Team.objects.filter(id=team_id).exists():
            raise serializers.ValidationError({"team_id": "Geçersiz takım ID'si."})
        return data

    def create(self, validated_data):
        team_id = validated_data.pop('team_id', None)
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        if team_id:
            team_instance = Team.objects.get(id=team_id)
            user.profile.team = team_instance
            user.profile.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})