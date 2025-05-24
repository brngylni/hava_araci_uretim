
import factory
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.envanter.factories import AircraftModelFactory, PartFactory, PartTypeFactory
from apps.envanter.models import Part, PartType
from apps.montaj.models import AssembledAircraft
from apps.uretim.factories import AssemblyTeamFactory, KanatTeamFactory
from apps.users.factories import UserFactory


class AssembledAircraftModelTest(TestCase):
    """AssembledAircraft modelinin __str__ ve save() metotlarının davranışlarını test eder."""
    def setUp(self):
        """Testler için gerekli olan temel model instance'larını oluşturur."""

        self.tb2_model = AircraftModelFactory(name='TB2_MODELTEST') # Model testine özel isim
        self.akinci_model = AircraftModelFactory(name='AKINCI_MODELTEST') # Kullanılmıyor, kaldırılabilir
        self.montaj_team = AssemblyTeamFactory(name='MONTAJ_TEAM_MODELTEST') # Model testine özel isim

        self.kanat_pt = PartTypeFactory(name='KANAT_MTM') # MTM: Model Test Montaj
        self.govde_pt = PartTypeFactory(name='GOVDE_MTM')
        self.kuyruk_pt = PartTypeFactory(name='KUYRUK_MTM')
        self.aviyonik_pt = PartTypeFactory(name='AVIYONIK_MTM')

        # Geçerli parçalar
        self.valid_wing = PartFactory(part_type=self.kanat_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA')
        self.valid_fuselage = PartFactory(part_type=self.govde_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA')
        self.valid_tail = PartFactory(part_type=self.kuyruk_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA')
        self.valid_avionics = PartFactory(part_type=self.aviyonik_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA')


    def test_str_representation(self):
        """AssembledAircraft instance'ının __str__ metodunun doğru formatı döndürdüğünü test eder."""
        aa = AssembledAircraft.objects.create(
            aircraft_model=self.tb2_model, tail_number="TC-STR-AA-01", assembled_by_team=self.montaj_team,
            wing=self.valid_wing, fuselage=self.valid_fuselage, tail=self.valid_tail, avionics=self.valid_avionics
        )
        expected_str_part = f"{self.tb2_model.get_name_display()} - TC-STR-AA-01 (Monte Edildi: {aa.assembly_date})"
        self.assertEqual(str(aa), expected_str_part)

    def test_save_method_on_create_updates_part_status(self):
        """Yeni bir AssembledAircraft kaydedildiğinde, kullanılan parçaların durumunun 'KULLANILDI' olarak güncellendiğini test eder."""

        aa = AssembledAircraft(
            aircraft_model=self.tb2_model,
            tail_number="TC-SAVE-CREATE-01",
            assembled_by_team=self.montaj_team,
            wing=self.valid_wing,
            fuselage=self.valid_fuselage,
            tail=self.valid_tail,
            avionics=self.valid_avionics
        )
        aa.save() # Bu, modelin save() metodunu ve içindeki is_new bloğunu tetikler.

        self.valid_wing.refresh_from_db()
        self.assertEqual(self.valid_wing.status, 'KULLANILDI')
        self.assertEqual(self.valid_wing.used_in_aircraft, aa)

        self.valid_fuselage.refresh_from_db()
        self.assertEqual(self.valid_fuselage.status, 'KULLANILDI')

    def test_save_method_on_update_does_not_change_part_status_if_parts_not_changed(self):
        """Mevcut bir AssembledAircraft güncellendiğinde (parçalar değişmeden), parçaların durumunun etkilenmediğini test eder."""
        aa = AssembledAircraft.objects.create(
            aircraft_model=self.tb2_model, tail_number="TC-SAVEUPD-01", assembled_by_team=self.montaj_team,
            wing=self.valid_wing, fuselage=self.valid_fuselage, tail=self.valid_tail, avionics=self.valid_avionics
        )
        self.valid_wing.refresh_from_db()
        initial_wing_status = self.valid_wing.status
        self.assertEqual(initial_wing_status, 'KULLANILDI') # Oluşturma sonrası KULLANILDI olmalı

        aa.tail_number = "TC-SAVEUPD-01-MOD" # Sadece kuyruk numarasını değiştir
        aa.save() # Bu, modelin save() metodunu çağırır, is_new=False olur.
        self.valid_wing.refresh_from_db()
        self.assertEqual(self.valid_wing.status, initial_wing_status) # Durum değişmemeli (hala KULLANILDI)


class AssembledAircraftAPITest(APITestCase):
    """AssembledAircraft API endpoint'lerinin (CRUD, check_missing_parts) işlevlerini test eder."""

    def setUp(self):
        """Testler için gerekli kullanıcıları, takımları, modelleri, parçaları ve URL'leri hazırlar."""
        self.montaj_team_user = UserFactory(username="montaj_api_user")  # Daha açıklayıcı username
        self.montaj_team = AssemblyTeamFactory()  # Standart MONTAJ takımı
        self.montaj_team_user.profile.team = self.montaj_team
        self.montaj_team_user.profile.save()

        self.kanat_team_user = UserFactory(username="kanat_api_user")
        self.kanat_team = KanatTeamFactory()  # Standart KANAT takımı
        self.kanat_team_user.profile.team = self.kanat_team
        self.kanat_team_user.profile.save()

        self.tb2_model = AircraftModelFactory(name='TB2')  # Standart model isimleri
        self.akinci_model = AircraftModelFactory(name='AKINCI')

        # PartType'ları standart isimlerle get_or_create ile alalım ki tutarlı olsun
        self.kanat_pt = PartType.objects.get_or_create(name='KANAT')[0]
        self.govde_pt = PartType.objects.get_or_create(name='GOVDE')[0]
        self.kuyruk_pt = PartType.objects.get_or_create(name='KUYRUK')[0]
        self.aviyonik_pt = PartType.objects.get_or_create(name='AVIYONIK')[0]

        self.assemble_url = reverse('assembledaircraft-list')
        self.check_missing_url = reverse('assembledaircraft-check-missing-parts')
        self.detail_url = lambda pk: reverse('assembledaircraft-detail', kwargs={'pk': pk})

    def _create_valid_parts_for_model(self, aircraft_model):
        """Belirli bir `aircraft_model` için STOKTA olan geçerli bir parça seti oluşturur."""
        parts = {
            'wing': PartFactory(part_type=self.kanat_pt, aircraft_model_compatibility=aircraft_model,status='STOKTA',
                                serial_number=factory.Sequence(lambda n: f"SN-WING-{aircraft_model.name}-{n}")),
            'fuselage': PartFactory(part_type=self.govde_pt, aircraft_model_compatibility=aircraft_model, status='STOKTA',
                                    serial_number=factory.Sequence(lambda n: f"SN-FUSE-{aircraft_model.name}-{n}")),
            'tail': PartFactory(part_type=self.kuyruk_pt, aircraft_model_compatibility=aircraft_model,status='STOKTA',
                                serial_number=factory.Sequence(lambda n: f"SN-TAIL-{aircraft_model.name}-{n}")),
            'avionics': PartFactory(part_type=self.aviyonik_pt, aircraft_model_compatibility=aircraft_model, status='STOKTA',
                                    serial_number=factory.Sequence(lambda n: f"SN-AVIO-{aircraft_model.name}-{n}")),
        }
        return parts

    def test_assemble_aircraft_by_assembly_team_success(self):
        """Montaj takımının, geçerli parçalarla başarılı bir şekilde uçak monte edebildiğini test eder."""
        self.client.force_authenticate(user=self.montaj_team_user)
        parts_for_this_aircraft = self._create_valid_parts_for_model(self.tb2_model)

        data = {
            "aircraft_model": self.tb2_model.id,
            "tail_number": "TC-ASM-SUCCESS-001",  # Eşsiz kuyruk no
            "wing": parts_for_this_aircraft['wing'].id,
            "fuselage": parts_for_this_aircraft['fuselage'].id,
            "tail": parts_for_this_aircraft['tail'].id,
            "avionics": parts_for_this_aircraft['avionics'].id
        }
        response = self.client.post(self.assemble_url, data, format='json')

        # Hata ayıklama için print ifadesi, sorun devam ederse açılabilir
        if response.status_code != status.HTTP_201_CREATED:
            print(f"DEBUG - test_assemble_aircraft_success - Response Data: {response.data}")
            print(
                f"DEBUG - Wing Part ({parts_for_this_aircraft['wing'].id}): Type={parts_for_this_aircraft['wing'].part_type}, Compatible={parts_for_this_aircraft['wing'].aircraft_model_compatibility}, Status={parts_for_this_aircraft['wing'].status}")


        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        assembled_aircraft = AssembledAircraft.objects.get(pk=response.data['id'])
        self.assertEqual(assembled_aircraft.tail_number, "TC-ASM-SUCCESS-001")
        self.assertEqual(assembled_aircraft.assembled_by_team, self.montaj_team)

        # Parçaların durumunu DB'den taze çekerek kontrol et
        wing_db = Part.objects.get(pk=parts_for_this_aircraft['wing'].id)
        self.assertEqual(wing_db.status, 'KULLANILDI')
        self.assertEqual(wing_db.used_in_aircraft, assembled_aircraft)


    def test_assemble_aircraft_by_production_team_forbidden(self):
        """Üretim takımının (montaj takımı olmayan) uçak monte etme girişiminin reddedildiğini test eder (403)."""
        self.client.force_authenticate(user=self.kanat_team_user)
        parts = self._create_valid_parts_for_model(self.tb2_model)  # Parçalar yine de oluşturulmalı
        data = {"aircraft_model": self.tb2_model.id, "tail_number": "TC-ASM-FORBID-001", "wing": parts['wing'].id,
                "fuselage": parts['fuselage'].id, "tail": parts['tail'].id, "avionics": parts['avionics'].id}
        response = self.client.post(self.assemble_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assemble_aircraft_with_missing_part(self):
        """Gerekli bir parça eksik olduğunda montaj girişiminin başarısız olduğunu (400) ve ilgili hata mesajını döndürdüğünü test eder."""
        self.client.force_authenticate(user=self.montaj_team_user)
        parts = self._create_valid_parts_for_model(self.tb2_model)
        data = {"aircraft_model": self.tb2_model.id, "tail_number": "TC-ASM-MISSING-001", "wing": parts['wing'].id,
                "fuselage": parts['fuselage'].id, "tail": parts['tail'].id}  # Aviyonik eksik
        response = self.client.post(self.assemble_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("avionics", response.data)
        self.assertTrue(any("alan zorunlu" in err for err in response.data['avionics']))

    def test_assemble_aircraft_with_incompatible_part(self):
        """Uçak modeliyle uyumsuz bir parça kullanıldığında montaj girişiminin başarısız olduğunu (400) ve ilgili hata mesajını döndürdüğünü test eder."""
        self.client.force_authenticate(user=self.montaj_team_user)
        valid_parts_for_tb2 = self._create_valid_parts_for_model(self.tb2_model)
        incompatible_wing = PartFactory(part_type=self.kanat_pt, aircraft_model_compatibility=self.akinci_model,
                                        status='STOKTA')

        data = {
            "aircraft_model": self.tb2_model.id, "tail_number": "TC-ASM-INCOMPAT-001",
            "wing": incompatible_wing.id,
            "fuselage": valid_parts_for_tb2['fuselage'].id,
            "tail": valid_parts_for_tb2['tail'].id,
            "avionics": valid_parts_for_tb2['avionics'].id
        }
        response = self.client.post(self.assemble_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("wing", response.data)
        self.assertTrue(any("uyumlu değil" in err_msg for err_msg in response.data['wing']))

    def test_assemble_aircraft_with_used_part(self):
        """Daha önce kullanılmış (stokta olmayan) bir parça ile montaj girişiminin başarısız olduğunu (400) test eder."""
        self.client.force_authenticate(user=self.montaj_team_user)
        parts = self._create_valid_parts_for_model(self.tb2_model)
        parts['wing'].status = 'KULLANILDI'  # Kanadı kullanılmış yapalım
        parts['wing'].save()

        data = {"aircraft_model": self.tb2_model.id, "tail_number": "TC-ASM-USED-001", "wing": parts['wing'].id,
                "fuselage": parts['fuselage'].id, "tail": parts['tail'].id, "avionics": parts['avionics'].id}
        response = self.client.post(self.assemble_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("wing", response.data)
        self.assertTrue(any(e.code == 'does_not_exist' or "stokta değil" in str(e) for e in response.data['wing']))

    def test_check_missing_parts_action_with_missing(self):
        """`check_missing_parts` action'ının, bazı temel parçalar eksik olduğunda doğru uyarıları verdiğini test eder."""
        Part.objects.filter(part_type=self.govde_pt, aircraft_model_compatibility=self.tb2_model).delete()
        _ = PartFactory(part_type=self.kanat_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA')
        _ = PartFactory(part_type=self.kuyruk_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA')
        _ = PartFactory(part_type=self.aviyonik_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA')

        self.client.force_authenticate(user=self.montaj_team_user)
        url_params = f'?aircraft_model_name={self.tb2_model.name}'
        response = self.client.get(self.check_missing_url + url_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("warnings", response.data)
        self.assertTrue(any(self.govde_pt.get_name_display() in w for w in response.data['warnings']))
        self.assertEqual(response.data['required_parts_check'][self.govde_pt.get_name_display()], 0)
        self.assertGreaterEqual(response.data['required_parts_check'][self.kanat_pt.get_name_display()], 1)

    def test_check_missing_parts_action_all_available(self):
        """`check_missing_parts` action'ının, tüm temel parçalar mevcut olduğunda uyarı vermediğini test eder."""
        self._create_valid_parts_for_model(self.tb2_model)

        self.client.force_authenticate(user=self.montaj_team_user)
        url_params = f'?aircraft_model_name={self.tb2_model.name}'
        response = self.client.get(self.check_missing_url + url_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertNotIn("warnings", response.data)
        self.assertTrue("tüm temel parçalardan en az birer adet stokta mevcut" in response.data.get("message", ""))
        for part_type_display_name, count in response.data['required_parts_check'].items():
            self.assertGreaterEqual(count, 1)

    def test_update_assembled_aircraft_tail_number(self):
        """Monte edilmiş bir uçağın sadece kuyruk numarasının güncellenebildiğini test eder."""
        self.client.force_authenticate(user=self.montaj_team_user)
        parts = self._create_valid_parts_for_model(self.tb2_model)
        aa = AssembledAircraft.objects.create(
            aircraft_model=self.tb2_model, tail_number="TC-UPD-TN-001",
            assembled_by_team=self.montaj_team_user.profile.team,
            wing=parts['wing'], fuselage=parts['fuselage'],
            tail=parts['tail'], avionics=parts['avionics']
        )

        data = {"tail_number": "TC-UPD-TN-001-NEW"}
        response = self.client.patch(self.detail_url(aa.pk), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        aa.refresh_from_db()
        self.assertEqual(aa.tail_number, "TC-UPD-TN-001-NEW")

    def test_update_assembled_aircraft_change_part_not_allowed_or_complex(self):
        """Monte edilmiş bir uçağın parçasını değiştirme senaryosunu test eder (mevcut implementasyonun davranışını)."""
        self.client.force_authenticate(user=self.montaj_team_user)
        parts_initial = self._create_valid_parts_for_model(self.tb2_model)
        aa = AssembledAircraft.objects.create(
            aircraft_model=self.tb2_model, tail_number="TC-CHGPRT-001",
            assembled_by_team=self.montaj_team_user.profile.team, **parts_initial
        )

        old_wing_id = parts_initial['wing'].id
        old_wing_from_db = Part.objects.get(pk=old_wing_id)
        self.assertEqual(old_wing_from_db.status, 'KULLANILDI')

        new_wing = PartFactory(part_type=self.kanat_pt, aircraft_model_compatibility=self.tb2_model, status='STOKTA',
                               serial_number="SN-NEW-WING-001")
        data = {"wing": new_wing.id}  # Sadece wing'i değiştirmeyi dene

        response = self.client.patch(self.detail_url(aa.pk), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        aa.refresh_from_db()
        self.assertEqual(aa.wing, new_wing)  # Yeni kanat atanmış olmalı

        new_wing.refresh_from_db()
        self.assertEqual(new_wing.status, 'KULLANILDI')  # Yeni kanat kullanıldı olmalı
        self.assertEqual(new_wing.used_in_aircraft, aa)

        old_wing_from_db.refresh_from_db()
        self.assertEqual(old_wing_from_db.status, 'STOKTA')  # Eski kanat stoğa dönmeli
        self.assertIsNone(old_wing_from_db.used_in_aircraft)

    def test_delete_assembled_aircraft_releases_parts(self):  # İsmi değiştirdim
        """Bir AssembledAircraft silindiğinde, kullanılan parçaların durumunun 'STOKTA' olarak güncellendiğini test eder."""
        self.client.force_authenticate(user=self.montaj_team_user)
        parts = self._create_valid_parts_for_model(self.tb2_model)
        aa = AssembledAircraft.objects.create(
            aircraft_model=self.tb2_model, tail_number="TC-DEL-REL-001",
            assembled_by_team=self.montaj_team_user.profile.team, **parts
        )
        part_ids_before_delete = [p.id for p in parts.values()]

        response = self.client.delete(self.detail_url(aa.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AssembledAircraft.objects.filter(pk=aa.pk).exists())

        for part_id in part_ids_before_delete:
            part_after_delete = Part.objects.get(pk=part_id)
            self.assertEqual(part_after_delete.status, 'STOKTA')
            self.assertIsNone(part_after_delete.used_in_aircraft)

    def test_check_missing_parts_non_existent_model_name(self):
        """`check_missing_parts` action'ına var olmayan bir uçak modeli adı gönderildiğinde 400 Bad Request aldığını test eder."""
        self.client.force_authenticate(user=self.montaj_team_user)
        url_params = '?aircraft_model_name=NONEXISTENTMODELXYZ'
        response = self.client.get(self.check_missing_url + url_params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('aircraft_model_name', response.data)
        self.assertTrue(any("geçerli bir seçim değil" in str(e) for e in response.data['aircraft_model_name']))


class AssembledAircraftModelLogicTest(TestCase):  # Yeni isim verdim
    """
    AssembledAircraft modelinin clean() ve save() metotlarındaki
    iş mantıklarını ve validasyonlarını test eder.
    """

    @classmethod
    def setUpTestData(cls):
        """Testler için gerekli olan ortak verileri sınıf seviyesinde bir kez oluşturur."""
        # Temel PartType'ları standart isimlerle oluşturalım
        cls.kanat_pt = PartType.objects.get_or_create(name='KANAT')[0]
        cls.govde_pt = PartType.objects.get_or_create(name='GOVDE')[0]
        cls.kuyruk_pt = PartType.objects.get_or_create(name='KUYRUK')[0]
        cls.aviyonik_pt = PartType.objects.get_or_create(name='AVIYONIK')[0]

        cls.tb2_model = AircraftModelFactory(name='TB2')
        cls.akinci_model = AircraftModelFactory(name='AKINCI')

        cls.montaj_team = AssemblyTeamFactory()
        cls.kanat_team = KanatTeamFactory()  # Parçaları üreten takım için

    def _create_valid_parts_for_model(self, aircraft_model, prefix="VALID"):
        """Belirli bir model için geçerli STOKTA parça seti oluşturur."""
        # Serial number'ların eşsiz olması için prefix kullanıyoruz
        wing = PartFactory(part_type=self.kanat_pt, aircraft_model_compatibility=aircraft_model,status='STOKTA',
                           serial_number=f"SN-{prefix}-W-{aircraft_model.name}", produced_by_team=self.kanat_team)
        fuselage = PartFactory(part_type=self.govde_pt, aircraft_model_compatibility=aircraft_model,status='STOKTA',
                               serial_number=f"SN-{prefix}-F-{aircraft_model.name}",
                               produced_by_team=self.kanat_team)  # Üreten takım önemli değil bu test için
        tail = PartFactory(part_type=self.kuyruk_pt, aircraft_model_compatibility=aircraft_model,status='STOKTA',
                           serial_number=f"SN-{prefix}-T-{aircraft_model.name}", produced_by_team=self.kanat_team)
        avionics = PartFactory(part_type=self.aviyonik_pt, aircraft_model_compatibility=aircraft_model,status='STOKTA',
                               serial_number=f"SN-{prefix}-A-{aircraft_model.name}", produced_by_team=self.kanat_team)
        return {'wing': wing, 'fuselage': fuselage, 'tail': tail, 'avionics': avionics}


    def test_clean_valid_data_no_error(self):
        """Geçerli parçalarla clean() metodunun hata fırlatmadığını test eder."""
        parts = self._create_valid_parts_for_model(self.tb2_model, prefix="CLEANVALID")
        aircraft = AssembledAircraft(
            aircraft_model=self.tb2_model, tail_number="TC-CV-01", assembled_by_team=self.montaj_team, **parts
        )
        try:
            aircraft.full_clean()  # clean() metodunu tetikler
        except ValidationError as e:
            self.fail(f"Valid data should not raise ValidationError: {e.message_dict}")

    def test_clean_missing_required_part_field(self):
        """clean() metodunun, yeni oluşturulan bir uçakta zorunlu bir parça alanı eksikse hata verdiğini test eder."""

        parts = self._create_valid_parts_for_model(self.tb2_model, prefix="CLEANMISS")
        aircraft_data = {
            'aircraft_model': self.tb2_model, 'tail_number': "TC-CM-01", 'assembled_by_team': self.montaj_team,
            'wing': parts['wing'], 'fuselage': parts['fuselage'], 'tail': parts['tail']
            # avionics eksik
        }
        aircraft = AssembledAircraft(**aircraft_data)
        with self.assertRaisesRegex(ValidationError, "atanmalıdır"):  # Veya field'a özel mesaj
            aircraft.full_clean()

    def test_clean_incorrect_part_type(self):
        """clean() metodunun, yanlış tipte bir parça atandığında ValidationError fırlattığını test eder."""
        parts = self._create_valid_parts_for_model(self.tb2_model, prefix="CLEANINCTYPE")
        wrong_type_for_wing = PartFactory(part_type=self.govde_pt, aircraft_model_compatibility=self.tb2_model,
                                          status='STOKTA', serial_number="SN-WRONGTYPE")  # Kanat yerine Gövde

        aircraft = AssembledAircraft(
            aircraft_model=self.tb2_model, tail_number="TC-CIT-01", assembled_by_team=self.montaj_team,
            wing=wrong_type_for_wing, fuselage=parts['fuselage'], tail=parts['tail'], avionics=parts['avionics']
        )
        with self.assertRaisesRegex(ValidationError, "yanlış tipte"):
            aircraft.full_clean()

    def test_clean_incompatible_aircraft_model_for_part(self):
        """clean() metodunun, uçağın modeliyle uyumlu olmayan bir parça atandığında ValidationError fırlattığını test eder."""
        parts = self._create_valid_parts_for_model(self.tb2_model, prefix="CLEANINCOMPAT")  # Diğer parçalar TB2 için
        incompatible_wing = PartFactory(part_type=self.kanat_pt, aircraft_model_compatibility=self.akinci_model,
                                        status='STOKTA', serial_number="SN-INCOMPAT")  # Akıncı kanadı

        aircraft = AssembledAircraft(
            aircraft_model=self.tb2_model, tail_number="TC-CIM-01", assembled_by_team=self.montaj_team,
            wing=incompatible_wing, fuselage=parts['fuselage'], tail=parts['tail'], avionics=parts['avionics']
        )
        with self.assertRaisesRegex(ValidationError, "uyumlu değil"):
            aircraft.full_clean()

    def test_clean_part_not_in_stock_for_new_aircraft(self):
        """clean() metodunun, yeni bir uçak için stokta olmayan bir parça atandığında ValidationError fırlattığını test eder."""
        parts = self._create_valid_parts_for_model(self.tb2_model, prefix="CLEANNOSTOCK")
        parts['wing'].status = 'KULLANILDI'  # Kanadı kullanılmış yap
        parts['wing'].save()

        aircraft = AssembledAircraft(
            aircraft_model=self.tb2_model, tail_number="TC-CNS-01", assembled_by_team=self.montaj_team,
            **parts
        )
        with self.assertRaisesRegex(ValidationError, "stokta değil"):
            aircraft.full_clean()

    def test_clean_same_part_for_multiple_roles(self):
        """clean() metodunun, aynı parçanın birden fazla role atanması durumunda ValidationError fırlattığını test eder."""
        parts = self._create_valid_parts_for_model(self.tb2_model, prefix="CLEANSAME")
        aircraft = AssembledAircraft(
            aircraft_model=self.tb2_model, tail_number="TC-CSM-01", assembled_by_team=self.montaj_team,
            wing=parts['wing'], fuselage=parts['wing'],  # Aynı kanat hem wing hem fuselage
            tail=parts['tail'], avionics=parts['avionics']
        )
        with self.assertRaisesRegex(ValidationError, "birden fazla rolde kullanılamaz"):
            aircraft.full_clean()

    # --- save() Metodu Testleri ---
    def test_save_new_aircraft_updates_part_statuses_and_relations(self):
        """Yeni bir AssembledAircraft kaydedildiğinde, save() metodunun kullanılan parçaların
        durumunu 'KULLANILDI' yaptığını ve used_in_aircraft ilişkisini kurduğunu test eder."""
        parts = self._create_valid_parts_for_model(self.tb2_model, prefix="SAVEVALID")
        aircraft = AssembledAircraft(
            aircraft_model=self.tb2_model, tail_number="TC-SNU-01", assembled_by_team=self.montaj_team,
            **parts
        )
        # Henüz save() çağrılmadı, parçalar STOKTA olmalı
        self.assertEqual(parts['wing'].status, 'STOKTA')

        aircraft.save()  # Bu, modelin save() metodunu ve içindeki is_new bloğunu tetikler.

        # Parçaları veritabanından taze çekerek kontrol et
        for part_key in parts:
            reloaded_part = Part.objects.get(pk=parts[part_key].pk)
            self.assertEqual(reloaded_part.status, 'KULLANILDI', f"{part_key} status should be KULLANILDI")
            self.assertEqual(reloaded_part.used_in_aircraft, aircraft, f"{part_key} should be linked to aircraft")

    def test_save_updated_aircraft_does_not_affect_parts_if_not_changed(self):
        """Mevcut bir AssembledAircraft'ın parçaları dışındaki bir alanı güncellendiğinde,
        save() metodunun parçaların durumunu etkilemediğini test eder."""
        parts_initial = self._create_valid_parts_for_model(self.tb2_model, prefix="SAVEUPDATE")
        aircraft = AssembledAircraft.objects.create(  # Önce uçağı oluşturalım
            aircraft_model=self.tb2_model, tail_number="TC-SUPD-01", assembled_by_team=self.montaj_team,
            **parts_initial
        )
        # Parçalar KULLANILDI olmalı
        wing_initial_db = Part.objects.get(pk=parts_initial['wing'].pk)
        self.assertEqual(wing_initial_db.status, 'KULLANILDI')

        aircraft.tail_number = "TC-SUPD-01-MODIFIED"
        aircraft.save()  # Bu save() çağrısında is_new False olacak.

        wing_after_update_db = Part.objects.get(pk=parts_initial['wing'].pk)
        self.assertEqual(wing_after_update_db.status, 'KULLANILDI', "Part status should remain KULLANILDI")
        self.assertEqual(wing_after_update_db.used_in_aircraft, aircraft)  # Hala aynı uçağa bağlı olmalı

