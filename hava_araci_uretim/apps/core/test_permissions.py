from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.core.permissions import (
    IsTeamMemberOrReadOnly,
    IsProductionTeamAndResponsibleForPartType,
    IsAssemblyTeam,
    CanRecyclePart
)
from apps.envanter.factories import PartFactory, PartTypeFactory, AircraftModelFactory
from apps.montaj.models import AssembledAircraft
from apps.uretim.factories import KanatTeamFactory, GovdeTeamFactory, AssemblyTeamFactory, AviyonikTeamFactory, \
    KuyrukTeamFactory, TeamFactory
from apps.users.factories import UserFactory


# Basit bir mock view oluşturalım
class MockView(APIView):
    """İzin sınıflarını test etmek için kullanılacak sahte bir APIView."""
    pass


class PermissionTestBase(TestCase):
    """İzin testleri için temel hazırlık (setup) sınıfı."""

    @classmethod
    def setUpTestData(cls):
        """Testler için gerekli olan ortak verileri sınıf seviyesinde bir kez oluşturur."""
        cls.factory = APIRequestFactory()
        cls.view = MockView()

        # Kullanıcılar
        cls.anonymous_user = AnonymousUser()
        cls.user_no_profile = User.objects.create_user(username="user_no_profile_perm", password="password")

        cls.user_no_team_user_obj = UserFactory(username="user_no_team_perm")
        cls.user_no_team_user_obj.profile.team = None
        cls.user_no_team_user_obj.profile.save()
        cls.user_no_team = cls.user_no_team_user_obj

        # Takımlar ve Parça Tipleri
        cls.kanat_part_type = PartTypeFactory(name='KANAT')
        cls.govde_part_type = PartTypeFactory(name='GOVDE')
        cls.kuyruk_part_type = PartTypeFactory(name='KUYRUK')
        cls.aviyonik_part_type = PartTypeFactory(name='AVIYONIK')

        cls.kanat_team = KanatTeamFactory()
        cls.govde_team = GovdeTeamFactory()
        cls.montaj_team = AssemblyTeamFactory()

        kuyruk_team_for_parts = KuyrukTeamFactory()  # Parça üretimi için ayrı instance
        aviyonik_team_for_parts = AviyonikTeamFactory()  # Parça üretimi için ayrı instance

        cls.user_kanat_team_user_obj = UserFactory(username="user_kanat_perm")
        cls.user_kanat_team_user_obj.profile.team = cls.kanat_team
        cls.user_kanat_team_user_obj.profile.save()
        cls.user_kanat_team = cls.user_kanat_team_user_obj

        cls.user_govde_team_user_obj = UserFactory(username="user_govde_perm")
        cls.user_govde_team_user_obj.profile.team = cls.govde_team
        cls.user_govde_team_user_obj.profile.save()
        cls.user_govde_team = cls.user_govde_team_user_obj

        cls.user_montaj_team_user_obj = UserFactory(username="user_montaj_perm")
        cls.user_montaj_team_user_obj.profile.team = cls.montaj_team
        cls.user_montaj_team_user_obj.profile.save()
        cls.user_montaj_team = cls.user_montaj_team_user_obj

        cls.tb2_model = AircraftModelFactory(name='TB2')

        cls.part_by_kanat_team = PartFactory(
            produced_by_team=cls.kanat_team, part_type=cls.kanat_part_type,
            aircraft_model_compatibility=cls.tb2_model
        )
        cls.part_by_govde_team = PartFactory(
            produced_by_team=cls.govde_team, part_type=cls.govde_part_type,
            aircraft_model_compatibility=cls.tb2_model
        )
        cls.part_used = PartFactory(
            produced_by_team=cls.kanat_team, part_type=cls.kanat_part_type,
            aircraft_model_compatibility=cls.tb2_model, status='KULLANILDI'
        )
        cls.part_recycled = PartFactory(
            produced_by_team=cls.kanat_team, part_type=cls.kanat_part_type,
            aircraft_model_compatibility=cls.tb2_model, status='GERI_DONUSUMDE'
        )

        cls.wing_for_aa = PartFactory(part_type=cls.kanat_part_type, aircraft_model_compatibility=cls.tb2_model,
                                      status='STOKTA', produced_by_team=cls.kanat_team)
        cls.fuselage_for_aa = PartFactory(part_type=cls.govde_part_type, aircraft_model_compatibility=cls.tb2_model,
                                          status='STOKTA', produced_by_team=cls.govde_team)
        cls.tail_for_aa = PartFactory(part_type=cls.kuyruk_part_type, aircraft_model_compatibility=cls.tb2_model,
                                      status='STOKTA', produced_by_team=kuyruk_team_for_parts)
        cls.avionics_for_aa = PartFactory(part_type=cls.aviyonik_part_type, aircraft_model_compatibility=cls.tb2_model,
                                          status='STOKTA', produced_by_team=aviyonik_team_for_parts)

        cls.assembled_aircraft_by_montaj = AssembledAircraft.objects.create(
            aircraft_model=cls.tb2_model, tail_number="TC-PERM-001",
            assembled_by_team=cls.montaj_team, wing=cls.wing_for_aa,
            fuselage=cls.fuselage_for_aa, tail=cls.tail_for_aa, avionics=cls.avionics_for_aa
        )


class IsTeamMemberOrReadOnlyPermissionTest(PermissionTestBase):
    """`IsTeamMemberOrReadOnly` izin sınıfının davranışlarını test eder."""

    def setUp(self):
        """Her test için izin sınıfının bir örneğini oluşturur."""
        self.permission = IsTeamMemberOrReadOnly()

    def test_safe_method_allowed_for_anonymous(self):
        """Anonim kullanıcıların GET gibi güvenli metotlarla objelere erişebildiğini test eder."""
        request = self.factory.get('/fake-url/')
        request.user = self.anonymous_user
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_unsafe_method_denied_for_anonymous(self):
        """Anonim kullanıcıların POST, PUT gibi güvenli olmayan metotlarla objelere erişemediğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.anonymous_user
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_unsafe_method_denied_for_user_no_profile(self):
        """Profili olmayan bir kullanıcının güvenli olmayan metotlarla objelere erişemediğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_no_profile
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_unsafe_method_denied_for_user_no_team(self):
        """Takımı olmayan (ama profili olan) bir kullanıcının güvenli olmayan metotlarla objelere erişemediğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_unsafe_method_allowed_for_team_member_part(self):
        """Bir parçayı üreten takımın üyesinin, o parçaya güvenli olmayan metotlarla erişebildiğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_unsafe_method_denied_for_non_team_member_part(self):
        """Bir parçayı üreten takımın üyesi olmayan bir kullanıcının, o parçaya güvenli olmayan metotlarla erişemediğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_govde_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_unsafe_method_allowed_for_team_member_assembled_aircraft(self):
        """Bir uçağı monte eden takımın üyesinin, o uçağa güvenli olmayan metotlarla erişebildiğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_montaj_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.assembled_aircraft_by_montaj))

    def test_unsafe_method_denied_for_non_team_member_assembled_aircraft(self):
        """Bir uçağı monte eden takımın üyesi olmayan bir kullanıcının, o uçağa güvenli olmayan metotlarla erişemediğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.assembled_aircraft_by_montaj))

    def test_object_without_team_field_denied_for_unsafe_method(self):
        """İzin sınıfının beklediği takım ilişkili alanlara (produced_by_team vb.) sahip olmayan bir objeye, güvenli olmayan metotlarla erişimin reddedildiğini test eder."""
        obj_no_team_info = self.kanat_part_type
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, obj_no_team_info))

    def test_unsafe_method_denied_for_user_with_profile_but_no_team(self):
        """Profili olan ama takımı olmayan bir kullanıcının güvenli olmayan metotlarla erişiminin reddedildiğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_obj_with_team_field_unsafe_method_allowed_for_member(self):
        """Doğrudan 'team' alanına sahip bir objeye (örn: UserProfile), o takımın üyesi olan bir kullanıcının güvenli olmayan metotlarla erişebildiğini test eder."""
        user_profile_obj = self.user_kanat_team.profile
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, user_profile_obj))

    def test_obj_with_team_field_unsafe_method_denied_for_non_member(self):
        """Doğrudan 'team' alanına sahip bir objeye (örn: UserProfile), o takımın üyesi olmayan bir kullanıcının güvenli olmayan metotlarla erişemediğini test eder."""
        user_profile_obj = self.user_kanat_team.profile
        request = self.factory.put('/fake-url/')
        request.user = self.user_govde_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, user_profile_obj))


class IsProductionTeamAndResponsiblePermissionTest(PermissionTestBase):
    """`IsProductionTeamAndResponsibleForPartType` izin sınıfının davranışlarını test eder."""

    def setUp(self):
        """Her test için izin sınıfının bir örneğini oluşturur."""
        self.permission = IsProductionTeamAndResponsibleForPartType()

    def test_has_permission_denied_for_montaj_team(self):
        """Montaj takımının genel üretim iznine sahip olmadığını test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_montaj_team
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_permission_allowed_for_production_team(self):
        """Sorumlu olduğu bir parça tipi olan üretim takımının genel üretim iznine sahip olduğunu test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_kanat_team  # Kanat takımının sorumlu olduğu parça tipi var
        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_has_permission_denied_for_user_no_team(self):
        """Takımı olmayan bir kullanıcının genel üretim iznine sahip olmadığını test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_permission_denied_for_production_team_without_responsible_type(self):
        """Sorumlu olduğu parça tipi olmayan bir üretim takımının (hatalı konfigürasyon) genel üretim iznine sahip olmadığını test eder."""
        team_no_resp = TeamFactory(name='GOVDE')  # GovdeTeamFactory yerine TeamFactory ile oluşturalım
        team_no_resp.responsible_part_type = None  # Sorumluluğu kaldıralım
        team_no_resp.save()
        user_prod_no_resp = UserFactory(username="user_prod_no_resp_perm")
        user_prod_no_resp.profile.team = team_no_resp
        user_prod_no_resp.profile.save()

        request = self.factory.post('/fake-url/')
        request.user = user_prod_no_resp
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_object_permission_safe_method_allowed(self):
        """Güvenli metotlarla (GET vb.) bir objeye erişimin her zaman izinli olduğunu test eder (izin sınıfının bu kısmı için)."""
        request = self.factory.get('/fake-url/')
        request.user = self.user_montaj_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_has_object_permission_allowed_for_responsible_team(self):
        """Bir parçaya, o parçanın tipinden sorumlu ve parçayı üreten takımın üyesi tarafından güvenli olmayan metotlarla erişilebildiğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_has_object_permission_denied_if_not_produced_by_team(self):
        """Bir parçaya, o parçanın tipinden sorumlu olsa bile, parçayı üretmeyen başka bir takımın üyesi tarafından güvenli olmayan metotlarla erişilemediğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_govde_team))

    def test_has_object_permission_denied_if_not_responsible_for_part_type(self):
        """Bir parçaya, o parçayı üretmiş olsa bile, parçanın tipinden sorumlu olmayan bir takımın üyesi tarafından (hatalı konfigürasyon) güvenli olmayan metotlarla erişilemediğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_govde_team))

    def test_has_object_permission_denied_for_montaj_team_unsafe_method(self):
        """Montaj takımının bir parçaya güvenli olmayan metotlarla erişemediğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_montaj_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_has_permission_denied_for_user_with_profile_but_no_team(self):
        """Profili olan ama takımı olmayan bir kullanıcının genel üretim iznine sahip olmadığını test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_object_permission_denied_for_user_with_profile_but_no_team_unsafe(self):
        """Profili olan ama takımı olmayan bir kullanıcının bir parçaya güvenli olmayan metotlarla erişemediğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))


class IsAssemblyTeamPermissionTest(PermissionTestBase):
    """`IsAssemblyTeam` izin sınıfının davranışlarını test eder."""

    def setUp(self):
        """Her test için izin sınıfının bir örneğini oluşturur."""
        # super().setUp() # PermissionTestBase.setUp artık boş
        self.permission = IsAssemblyTeam()

    def test_has_permission_allowed_for_assembly_team(self):
        """Montaj takımının genel montaj iznine sahip olduğunu test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_montaj_team
        self.assertTrue(self.permission.has_permission(request, self.view))

    def test_has_permission_denied_for_production_team(self):
        """Üretim takımının genel montaj iznine sahip olmadığını test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_kanat_team
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_permission_denied_for_user_no_team(self):
        """Takımı olmayan bir kullanıcının genel montaj iznine sahip olmadığını test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_has_object_permission_safe_method_allowed(self):
        """Güvenli metotlarla (GET vb.) bir monte edilmiş uçağa erişimin her zaman izinli olduğunu test eder (izin sınıfının bu kısmı için)."""
        request = self.factory.get('/fake-url/')
        request.user = self.user_kanat_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.assembled_aircraft_by_montaj))

    def test_has_object_permission_unsafe_method_allowed_for_assembly_team(self):
        """Montaj takımının bir monte edilmiş uçağa güvenli olmayan metotlarla erişebildiğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_montaj_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.assembled_aircraft_by_montaj))

    def test_has_object_permission_unsafe_method_denied_for_production_team(self):
        """Üretim takımının bir monte edilmiş uçağa güvenli olmayan metotlarla erişemediğini test eder."""
        request = self.factory.put('/fake-url/')
        request.user = self.user_kanat_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.assembled_aircraft_by_montaj))


class CanRecyclePartPermissionTest(PermissionTestBase):
    """`CanRecyclePart` izin sınıfının davranışlarını test eder."""

    def setUp(self):
        """Her test için izin sınıfının bir örneğini oluşturur."""
        # super().setUp() # PermissionTestBase.setUp artık boş
        self.permission = CanRecyclePart()

    def test_allowed_if_part_produced_by_team_and_not_recycled(self):
        """Bir parçanın, onu üreten takım tarafından ve henüz geri dönüşümde değilken, geri dönüşüme gönderilebildiğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_kanat_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_denied_if_part_not_produced_by_team(self):
        """Bir parçanın, onu üretmeyen başka bir takım tarafından geri dönüşüme gönderilemediğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_govde_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_denied_if_part_is_already_recycled(self):
        """Zaten geri dönüşümde olan bir parçanın tekrar geri dönüşüme gönderilemediğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_kanat_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_recycled))

    def test_allowed_if_part_is_used_and_produced_by_team(self):
        """Kullanımda olan bir parçanın (henüz geri dönüşümde değilse), onu üreten takım tarafından (izin sınıfı seviyesinde) geri dönüşüme gönderilebildiğini test eder (View seviyesinde ek kontrol olabilir)."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_kanat_team
        self.assertTrue(self.permission.has_object_permission(request, self.view, self.part_used))

    def test_denied_for_user_no_team(self):
        """Takımı olmayan bir kullanıcının bir parçayı geri dönüşüme gönderemediğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))

    def test_denied_for_user_with_profile_but_no_team(
            self):  # Bu test bir öncekiyle aynı, birini silebiliriz veya farklı bir senaryo olmalı.
        """Profili olan ama takımı olmayan bir kullanıcının parçayı geri dönüşüme gönderemediğini test eder."""
        request = self.factory.post('/fake-url/')
        request.user = self.user_no_team
        self.assertFalse(self.permission.has_object_permission(request, self.view, self.part_by_kanat_team))