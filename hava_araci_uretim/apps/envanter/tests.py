from unittest import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.envanter.models import Part
from apps.envanter.models import PartType
from apps.uretim.factories import KanatTeamFactory, GovdeTeamFactory
from apps.users.factories import UserFactory, AdminUserFactory
from .factories import PartTypeFactory, AircraftModelFactory, PartFactory


class PartModelStrTest(TestCase):
    def setUp(self):
        self.kanat_pt = PartTypeFactory(name='KANAT')
        self.govde_pt = PartTypeFactory(name='GOVDE')
        self.tb2_model = AircraftModelFactory(name='TB2')
        self.kanat_team = KanatTeamFactory()

    def test_part_str_representation(self):
        """Part modelinin __str__ metodunun doğru formatı ve okunabilir değerleri döndürdüğünü test eder."""
        part = PartFactory(
            part_type=self.kanat_pt,
            aircraft_model_compatibility=self.tb2_model,
            serial_number="SN-STR-001",
            status='STOKTA',
            produced_by_team=self.kanat_team
        )
        expected_str = f"{self.kanat_pt.get_name_display()} ({self.tb2_model.get_name_display()}) - SN: SN-STR-001 [Stokta]"
        self.assertEqual(str(part), expected_str)

    def test_part_str_representation_kullanildi(self):
        """Kullanılmış bir parça için __str__ metodunun doğru formatı döndürdüğünü test eder."""
        part = PartFactory(
            part_type=self.govde_pt,
            aircraft_model_compatibility=self.tb2_model,
            serial_number="SN-STR-002",
            status='KULLANILDI', # Manuel set
            produced_by_team=GovdeTeamFactory()
        )

        expected_str = f"{self.govde_pt.get_name_display()} ({self.tb2_model.get_name_display()}) - SN: SN-STR-002 [Kullanıldı]"
        self.assertEqual(str(part), expected_str)

class PartTypeAPITest(APITestCase):
    """PartType API endpoint'lerinin temel işlevlerini test eder."""
    def setUp(self):
        """Testler için kullanıcı ve PartType örnekleri oluşturur."""
        self.user = UserFactory()
        self.kanat_type = PartTypeFactory(name='KANAT')
        self.govde_type = PartTypeFactory(name='GOVDE')
        PartTypeFactory(name='KUYRUK')
        PartTypeFactory(name='AVIYONIK')
        self.part_types_list_url = reverse('parttype-list')
        self.part_type_detail_url = lambda pk: reverse('parttype-detail', kwargs={'pk':pk})


    def test_list_part_types_unauthenticated(self):
        """Kimliği doğrulanmamış bir kullanıcının parça tiplerini listeleyemediğini test eder (401)."""
        response = self.client.get(self.part_types_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_part_types_authenticated(self):
        """Kimliği doğrulanmış bir kullanıcının parça tiplerini listeleyebildiğini test eder (200)."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.part_types_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4) # setUp'ta 4 tane oluşturuldu.

    def test_retrieve_part_type_authenticated(self):
        """Kimliği doğrulanmış bir kullanıcının belirli bir parça tipinin detaylarını görebildiğini test eder."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.part_type_detail_url(self.kanat_type.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.kanat_type.name)
        self.assertEqual(response.data['get_name_display'], self.kanat_type.get_name_display())


class PartAPITest(APITestCase):
    """Part API endpoint'lerinin (CRUD, recycle) işlevlerini test eder."""

    def setUp(self):
        """Testler için gerekli kullanıcıları, takımları, parça tiplerini, uçak modellerini ve URL'leri hazırlar."""

        self.kanat_pt = PartTypeFactory(name='KANAT')
        self.govde_pt = PartTypeFactory(name='GOVDE')
        # ... diğer pt'ler ...
        self.kanat_team = KanatTeamFactory()  # Bu name='KANAT' ve KANAT PT'den sorumlu
        self.govde_team = GovdeTeamFactory()  # Bu name='GOVDE' ve GOVDE PT'den sorumlu
        # ... diğer team'ler ...
        self.admin_user = AdminUserFactory()
        self.kanat_team_user = UserFactory(username="user_kanat_partapi_v3")  # Eşsiz username
        self.kanat_team_user.profile.team = self.kanat_team
        self.kanat_team_user.profile.save()

        self.govde_team_user = UserFactory(username="user_govde_partapi_v3")  # Eşsiz username
        self.govde_team_user.profile.team = self.govde_team
        self.govde_team_user.profile.save()

        # ... diğer kullanıcılar ...
        self.tb2_model = AircraftModelFactory(name='TB2')
        self.akinci_model = AircraftModelFactory(name='AKINCI')
        self.parts_list_url = reverse('part-list')
        self.detail_url = lambda pk: reverse('part-detail', kwargs={'pk': pk})
        self.recycle_url = lambda pk: reverse('part-recycle', kwargs={'pk': pk})
        self.part_data_kanat_tb2_template = {  # Şablon olarak isimlendirelim
            "part_type": self.kanat_pt.id,
            "aircraft_model_compatibility": self.tb2_model.id
        }

    def test_create_part_by_responsible_team(self):
        """Sorumlu takımın, doğru parça tipi ve uçak modeli uyumluluğu ile parça üretebildiğini test eder."""
        self.client.force_authenticate(user=self.kanat_team_user)
        data = self.part_data_kanat_tb2_template.copy()
        data['serial_number'] = "SN-CREATE-RESP-UNIQUE-001"  # Her test için eşsiz SN

        response = self.client.post(self.parts_list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         f"Hata: {response.data}. Kullanıcı Takımı Sorumlu PT: {self.kanat_team_user.profile.team.responsible_part_type}, İstenen PT: {PartType.objects.get(id=data['part_type'])}")

        created_part = Part.objects.get(serial_number=data['serial_number'])
        self.assertEqual(created_part.produced_by_team, self.kanat_team)
        self.assertEqual(created_part.status, 'STOKTA')
        self.assertEqual(self.tb2_model, created_part.aircraft_model_compatibility)

    def test_recycle_part_by_producing_team(self):
        """Üreten takımın, stokta olan bir parçayı geri dönüşüme gönderebildiğini test eder."""
        self.client.force_authenticate(user=self.kanat_team_user)
        data_for_recycle = self.part_data_kanat_tb2_template.copy()
        data_for_recycle['serial_number'] = "SN-RECYCLE-PROD-UNIQUE-001"
        response_create = self.client.post(self.parts_list_url, data_for_recycle, format='json')
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED, response_create.data)
        part = Part.objects.get(serial_number=data_for_recycle['serial_number'])

        response_recycle = self.client.post(self.recycle_url(part.pk))
        self.assertEqual(response_recycle.status_code, status.HTTP_200_OK, response_recycle.data)
        part.refresh_from_db()
        self.assertEqual(part.status, 'GERI_DONUSUMDE')

    def test_recycle_part_by_other_team_forbidden(self):
        """Başka bir üretim takımının, kendisinin üretmediği bir parçayı geri dönüşüme gönderemediğini test eder."""
        self.client.force_authenticate(user=self.kanat_team_user)
        data_for_recycle_other = self.part_data_kanat_tb2_template.copy()
        data_for_recycle_other['serial_number'] = "SN-RECYCLE-OTHER-UNIQUE-001"
        response_create = self.client.post(self.parts_list_url, data_for_recycle_other, format='json')
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED, response_create.data)
        part = Part.objects.get(serial_number=data_for_recycle_other['serial_number'])

        self.client.force_authenticate(user=self.govde_team_user)
        response = self.client.post(self.recycle_url(part.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_part_by_admin(self):
        """Admin yetkisine sahip bir kullanıcının bir parçayı silebildiğini test eder."""
        self.client.force_authenticate(user=self.kanat_team_user)
        data_for_delete_admin = self.part_data_kanat_tb2_template.copy()
        data_for_delete_admin['serial_number'] = "SN-DEL-ADMIN-P-UNIQUE-001"
        response_create = self.client.post(self.parts_list_url, data_for_delete_admin, format='json')
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED, response_create.data)
        part = Part.objects.get(serial_number=data_for_delete_admin['serial_number'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(part.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Part.objects.filter(pk=part.pk).exists())


    def test_delete_part_by_non_admin_forbidden(self):
        """Admin yetkisine sahip olmayan bir kullanıcının bir parçayı silemediğini test eder."""
        self.client.force_authenticate(user=self.kanat_team_user)
        data_for_delete_non_admin = self.part_data_kanat_tb2_template.copy()
        data_for_delete_non_admin['serial_number'] = "SN-DEL-NONADMIN-P-UNIQUE-001"
        response_create = self.client.post(self.parts_list_url, data_for_delete_non_admin, format='json')
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED, response_create.data)
        part = Part.objects.get(serial_number=data_for_delete_non_admin['serial_number'])

        response = self.client.delete(self.detail_url(part.pk))  # Authenticated user hala kanat_team_user
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_list_parts_with_filters(self):
        """Parça listeleme endpoint'inin doğru filtrelerle çalıştığını test eder."""
        self.client.force_authenticate(user=self.kanat_team_user)


        PartFactory(serial_number="FILTER_PART_01", part_type=self.kanat_pt,
                    aircraft_model_compatibility=self.tb2_model, status='STOKTA', produced_by_team=self.kanat_team)
        PartFactory(serial_number="FILTER_PART_02", part_type=self.govde_pt,
                    aircraft_model_compatibility=self.tb2_model, status='STOKTA', produced_by_team=self.govde_team)
        part3 = PartFactory(serial_number="FILTER_PART_03", part_type=self.kanat_pt,
                            aircraft_model_compatibility=self.akinci_model, status='STOKTA',
                            produced_by_team=self.kanat_team)
        part3.status = 'KULLANILDI'  # Durumunu sonradan değiştir
        part3.save()


        response = self.client.get(self.parts_list_url, {'part_type': self.kanat_pt.id, 'status': 'STOKTA'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['serial_number'], "FILTER_PART_01")


    def test_update_part_with_invalid_data(self):
        """Geçersiz veri ile parça güncelleme denemesinin 400 Bad Request döndürdüğünü test eder."""
        self.client.force_authenticate(user=self.kanat_team_user)
        create_data = self.part_data_kanat_tb2_template.copy()
        create_data['serial_number'] = "SN-UPDATE-INVALID-UNIQUE-001"
        response_create = self.client.post(self.parts_list_url, create_data, format='json')
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED, response_create.data)
        part_id = response_create.data['id']

        data_to_update = {"part_type": 9999}  # Geçersiz PartType ID'si
        response = self.client.patch(self.detail_url(part_id), data_to_update, format='json')


        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         f"Beklenen 400, Alınan {response.status_code}, Data: {response.data}")
        self.assertIn("part_type", response.data)
        self.assertTrue(any(e.code == 'does_not_exist' for e in response.data['part_type']))