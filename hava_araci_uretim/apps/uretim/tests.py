from unittest import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.envanter.factories import PartTypeFactory
from apps.envanter.models import PartType
from apps.uretim.factories import TeamFactory, KanatTeamFactory, AssemblyTeamFactory
from apps.uretim.models import Team
from apps.users.factories import AdminUserFactory, UserFactory


class TeamModelTest(TestCase):
    """Team modelinin __str__ ve can_produce_part_type metotlarının davranışlarını test eder."""

    def setUp(self):
        """Testler için gerekli olan temel PartType ve Team instance'larını oluşturur."""
        self.kanat_pt = PartTypeFactory(name='KANAT')
        self.govde_pt = PartTypeFactory(name='GOVDE')

        self.montaj_team_no_pt = AssemblyTeamFactory()
        self.kanat_team_with_pt = KanatTeamFactory()


    def test_str_representation_production_team(self):
        """Bir üretim takımının __str__ metodunun doğru okunabilir adı döndürdüğünü test eder."""
        team = KanatTeamFactory()
        self.assertEqual(str(team), "Kanat Takımı")

    def test_str_representation_assembly_team(self):
        """Montaj takımının __str__ metodunun doğru okunabilir adı döndürdüğünü test eder."""
        team = AssemblyTeamFactory()
        self.assertEqual(str(team), "Montaj Takımı")

    def test_can_produce_part_type_true_for_responsible_team(self):
        """Bir üretim takımının, sorumlu olduğu parça tipini üretebildiğini test eder."""
        self.assertTrue(self.kanat_team_with_pt.can_produce_part_type(self.kanat_pt))

    def test_can_produce_part_type_false_for_wrong_part_type(self):  # Metot adını güncelledim
        """Bir üretim takımının, sorumlu olmadığı farklı bir parça tipini üretemediğini test eder."""
        self.assertFalse(self.kanat_team_with_pt.can_produce_part_type(self.govde_pt))

    def test_can_produce_part_type_false_for_assembly_team(self):
        """Montaj takımının herhangi bir parça tipini üretemediğini test eder."""
        self.assertFalse(self.montaj_team_no_pt.can_produce_part_type(self.kanat_pt))
        self.assertFalse(
            self.montaj_team_no_pt.can_produce_part_type(self.govde_pt))  # Farklı bir tiple de test edelim.

    def test_can_produce_part_type_false_if_team_has_no_responsible_type(self):
        """Sorumlu olduğu parça tipi olmayan bir üretim takımının (hatalı durum) parça üretemediğini test eder."""
        test_team_no_resp = TeamFactory(name='MONTAJ', responsible_part_type=None)
        self.assertFalse(test_team_no_resp.can_produce_part_type(self.govde_pt))

    def test_can_produce_part_type_with_none_part_type_instance(self):
        """`can_produce_part_type` metoduna None parça tipi gönderildiğinde False döndürdüğünü test eder (savunmacı)."""
        self.assertFalse(self.kanat_team_with_pt.can_produce_part_type(None))
        self.assertFalse(self.montaj_team_no_pt.can_produce_part_type(None))

class TeamAPITest(APITestCase):
    """Team API endpoint'lerinin (CRUD) işlevlerini ve izinlerini test eder."""
    def setUp(self):
        """Testler için admin ve normal kullanıcıları, PartType'ları ve URL'leri hazırlar."""
        self.admin_user = AdminUserFactory()
        self.regular_user = UserFactory()
        self.teams_list_url = reverse('team-list') # Create ve List için
        self.team_detail_url = lambda pk: reverse('team-detail', kwargs={'pk':pk}) # Retrieve, Update, Delete için

        self.kanat_pt = PartType.objects.get_or_create(name='KANAT')[0]
        self.govde_pt = PartType.objects.get_or_create(name='GOVDE')[0]
        self.kuyruk_pt = PartType.objects.get_or_create(name='KUYRUK')[0]

    def test_list_teams_as_admin(self):
        """Admin kullanıcının takımları listeleyebildiğini (200 OK) test eder."""
        KanatTeamFactory()
        AssemblyTeamFactory()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.teams_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['count'] >= 2) # Sayfalama için count

    def test_list_teams_as_regular_user_forbidden(self):
        """Normal bir kullanıcının takımları listeleyemediğini (403 Forbidden) test eder."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.teams_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_production_team_as_admin_success(self): # test_create_team_as_admin'i bölelim
        """Admin kullanıcının geçerli bir üretim takımı oluşturabildiğini (201 Created) test eder."""
        self.client.force_authenticate(user=self.admin_user)
        valid_data = {
            "name": "KUYRUK",
            "responsible_part_type": self.kuyruk_pt.id
        }
        response = self.client.post(self.teams_list_url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created_team = Team.objects.get(name="KUYRUK")
        self.assertEqual(created_team.responsible_part_type, self.kuyruk_pt)

    def test_create_assembly_team_as_admin_success(self):
        """Admin kullanıcının bir montaj takımı (responsible_part_type olmadan) oluşturabildiğini (201) test eder."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "MONTAJ"}
        response = self.client.post(self.teams_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        created_team = Team.objects.get(name="MONTAJ")
        self.assertIsNone(created_team.responsible_part_type)

    def test_create_team_name_part_type_mismatch_as_admin(self):
        """Admin kullanıcının, takım adı (tipi) ile sorumlu parça tipi uyuşmayan bir takım oluşturma girişiminin başarısız olduğunu (400) test eder."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "name": "KUYRUK",
            "responsible_part_type": self.kanat_pt.id
        }
        response = self.client.post(self.teams_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("responsible_part_type", response.data)
        self.assertTrue(any("sadece kendi tipindeki parçalardan sorumlu olabilir" in str(e) for e in response.data['responsible_part_type']))


    def test_create_production_team_without_responsible_part_type_as_admin(self):
        """Admin kullanıcının, bir üretim takımı için sorumlu parça tipi belirtmeden takım oluşturma girişiminin başarısız olduğunu (400) test eder."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "KANAT"} # responsible_part_type eksik
        response = self.client.post(self.teams_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("responsible_part_type", response.data)
        self.assertTrue(any("belirtilmelidir" in str(e) for e in response.data['responsible_part_type']))

    def test_create_assembly_team_with_responsible_part_type_as_admin(self):
        """Admin kullanıcının, bir montaj takımı için sorumlu parça tipi belirterek takım oluşturma girişiminin başarısız olduğunu (400) test eder."""
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "MONTAJ", "responsible_part_type": self.kanat_pt.id}
        response = self.client.post(self.teams_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("responsible_part_type", response.data)
        self.assertTrue(any("olamaz" in str(e) for e in response.data['responsible_part_type']))


    def test_create_team_as_regular_user_forbidden(self):
        """Normal bir kullanıcının takım oluşturamadığını (403 Forbidden) test eder."""
        self.client.force_authenticate(user=self.regular_user)
        data = {"name": "KUYRUK", "responsible_part_type": self.kuyruk_pt.id}
        response = self.client.post(self.teams_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_team_as_admin(self):
        """Admin kullanıcının belirli bir takımın detaylarını görebildiğini test eder."""
        team = KanatTeamFactory()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.team_detail_url(team.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], team.name)

    def test_update_team_name_and_responsible_type_as_admin(self):
        """Admin kullanıcının bir takımın adını (tipini) ve sorumlu parça tipini güncelleme senaryolarını test eder."""
        team_to_update = KanatTeamFactory() # Başlangıçta Kanat takımı
        self.client.force_authenticate(user=self.admin_user)

        data_invalid_update = {"responsible_part_type": self.govde_pt.id} # Kanat takımı ama Gövde PT
        response = self.client.patch(self.team_detail_url(team_to_update.pk), data_invalid_update, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         "Kanat takımına Gövde PT atanmamalıydı.")
        self.assertIn("responsible_part_type", response.data)


    def test_delete_team_as_admin(self):
        """Admin kullanıcının bir takımı silebildiğini test eder."""
        team_to_delete = AssemblyTeamFactory()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.team_detail_url(team_to_delete.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Team.objects.filter(pk=team_to_delete.pk).exists())