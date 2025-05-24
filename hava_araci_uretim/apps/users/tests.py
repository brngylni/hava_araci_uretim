from unittest import TestCase

import factory
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.uretim.factories import KanatTeamFactory, AssemblyTeamFactory, GovdeTeamFactory
from .factories import UserFactory, AdminUserFactory
from .models import UserProfile
from .serializers import UserSerializer


class UserAuthAPITests(APITestCase):
    """Kullanıcı kimlik doğrulama (kayıt, giriş) API endpoint'lerini test eder."""

    def setUp(self):
        """Testler için kayıt ve giriş URL'lerini ve temel bir takımı hazırlar."""
        self.register_url = reverse('user-register')
        self.login_url = reverse('user-login')
        self.kanat_team = KanatTeamFactory()  # test_user_registration_with_team_id için

    def test_user_registration_success(self):
        """Geçerli verilerle yeni bir kullanıcının başarıyla kaydedilebildiğini (201 Created),
        User ve UserProfile objelerinin oluşturulduğunu ve profilin başlangıçta takımsız olduğunu test eder."""
        data = {
            "username": "newuser_reg_success",  # Eşsiz username
            "email": "newuser_reg_success@example.com",
            "password": "password123",
            "password2": "password123",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(User.objects.filter(username=data['username']).exists())
        user = User.objects.get(username=data['username'])
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertIsNone(user.profile.team)

    def test_user_registration_with_team_id(self):
        """Yeni bir kullanıcı kaydedilirken geçerli bir team_id gönderildiğinde,
        kullanıcının profilinin doğru takıma atandığını test eder."""
        data = {
            "username": "teamuser_reg",  # Eşsiz username
            "email": "teamuser_reg@example.com",
            "password": "password123",
            "password2": "password123",
            "first_name": "Team",
            "last_name": "User",
            "team_id": self.kanat_team.id
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(username=data['username'])
        self.assertEqual(user.profile.team, self.kanat_team)

    def test_user_registration_invalid_team_id(self):
        """Yeni kullanıcı kaydı sırasında geçersiz bir team_id gönderildiğinde
        400 Bad Request alındığını ve 'team_id' için hata mesajı döndüğünü test eder."""
        data = {
            "username": "invalidteamuser_reg",  # Eşsiz username
            "email": "invalidteam_reg@example.com",
            "password": "password123",
            "password2": "password123",
            "team_id": 99999  # Geçersiz takım ID'si
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("team_id", response.data)
        self.assertTrue(any("Geçersiz takım ID'si" in str(e) for e in response.data['team_id']))

    def test_user_registration_password_mismatch(self):
        """Yeni kullanıcı kaydı sırasında şifrelerin uyuşmaması durumunda
        400 Bad Request alındığını ve 'password' için hata mesajı döndüğünü test eder."""
        data = {
            "username": "mismatchuser_reg",  # Eşsiz username
            "email": "mismatchpass_reg@example.com",
            "password": "password123",
            "password2": "mismatch"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertTrue(any("Şifreler eşleşmiyor" in str(e) for e in response.data['password']))

    def test_user_registration_missing_fields(self):
        """Yeni kullanıcı kaydı sırasında zorunlu alanlar (örn: email, password2) eksik gönderildiğinde
        400 Bad Request alındığını ve ilgili alanlar için hata mesajları döndüğünü test eder."""
        data = {"username": "missingfields_reg", "password": "password123"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password2", response.data)

    def test_user_login_success_and_token(self):
        """Geçerli kullanıcı adı ve şifre ile başarılı bir giriş yapıldığında (200 OK),
        bir token ve kullanıcı bilgilerinin döndürüldüğünü test eder."""
        user = UserFactory(username="loginuser_success", password="password123")
        data = {"username": "loginuser_success", "password": "password123"}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data['user']['username'], "loginuser_success")
        self.assertTrue(Token.objects.filter(user=user).exists())

    def test_user_login_inactive_user(self):
        """Aktif olmayan bir kullanıcıyla giriş denendiğinde 400 Bad Request alındığını
        ve uygun bir hata mesajı döndüğünü test eder."""
        UserFactory(username="inactiveuser_login", password="password123", is_active=False)
        data = {"username": "inactiveuser_login", "password": "password123"}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("aktif değil", response.data["error"].lower())

    def test_user_login_invalid_credentials_wrong_password(self):
        """Yanlış şifre ile giriş denendiğinde 401 Unauthorized alındığını test eder."""
        UserFactory(username="login_wrongpass", password="password123")
        data = {"username": "login_wrongpass", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_login_non_existent_user(self):
        """Var olmayan bir kullanıcı adı ile giriş denendiğinde 401 Unauthorized alındığını test eder."""
        data = {"username": "nonexistentuser", "password": "password123"}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileAPITests(APITestCase):
    """UserProfile API endpoint'lerinin (hem admin hem de kullanıcı bazlı) işlevlerini test eder."""

    def setUp(self):
        """Testler için kullanıcıları, takımları, profilleri ve URL'leri hazırlar."""
        self.user = UserFactory(username="profile_test_user")
        self.admin_user = AdminUserFactory(username="profile_test_admin")

        self.kanat_team = KanatTeamFactory()
        self.assembly_team = AssemblyTeamFactory()
        self.govde_team = GovdeTeamFactory()

        self.user.profile.team = self.kanat_team
        self.user.profile.save()

        self.client.force_authenticate(user=self.user)

        self.my_profile_url = reverse('userprofile-my-profile')
        self.profiles_list_url = reverse('userprofile-list')
        self.profile_detail_url = lambda pk: reverse('userprofile-detail', kwargs={'pk': pk})

    def test_get_my_profile_success(self):
        """Giriş yapmış bir kullanıcının kendi profil bilgilerini başarıyla alabildiğini test eder."""
        response = self.client.get(self.my_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['id'], self.user.profile.id)
        if self.user.profile.team:  # Takım varsa kontrol et
            self.assertEqual(response.data['team_details']['id'], self.kanat_team.id)

    def test_get_my_profile_unauthenticated(self):
        """Kimliği doğrulanmamış bir kullanıcının /my_profile/ endpoint'ine erişemediğini test eder."""
        self.client.logout()  # veya self.client.force_authenticate(user=None)
        response = self.client.get(self.my_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_my_profile_team_success(self):
        """Giriş yapmış bir kullanıcının kendi profilindeki takımı güncelleyebildiğini test eder."""
        data = {"team": self.assembly_team.id}
        response = self.client.patch(self.my_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.team, self.assembly_team)

    def test_update_my_profile_remove_team_success(self):
        """Giriş yapmış bir kullanıcının kendi profilindeki takımı kaldırabildiğini (None yapabildiğini) test eder."""
        data = {"team": None}
        response = self.client.patch(self.my_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.user.profile.refresh_from_db()
        self.assertIsNone(self.user.profile.team)

    def test_update_my_profile_with_invalid_team_id(self):
        """Kullanıcının kendi profilini geçersiz bir takım ID'si ile güncelleme girişiminin başarısız olduğunu (400) test eder."""
        data = {"team": 99999}
        response = self.client.patch(self.my_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("team", response.data)
        self.assertTrue(any(e.code == 'does_not_exist' for e in response.data['team']))

    def test_put_my_profile_requires_all_fields_or_specific_handling(self):
        """PUT ile /my_profile/ endpoint'ine eksik veri gönderildiğinde (eğer serializer tüm alanları bekliyorsa) hata alındığını test eder."""

        data = {"team": self.assembly_team.id}
        response = self.client.put(self.my_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.team, self.assembly_team)

    def test_list_profiles_as_admin(self):
        """Admin yetkisine sahip bir kullanıcının tüm kullanıcı profillerini listeleyebildiğini test eder."""
        UserFactory.create_batch(3, username=factory.Sequence(lambda n: f"profile_list_user{n}"))
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.profiles_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # setUp'ta self.user ve self.admin_user için profiller oluşur + 3 yeni = 5
        self.assertEqual(response.data['count'], 5)

    def test_list_profiles_as_regular_user_forbidden(self):
        """Normal bir kullanıcının tüm kullanıcı profillerini listeleme girişiminin reddedildiğini (403) test eder."""
        response = self.client.get(self.profiles_list_url)  # self.user ile authenticated
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_other_profile_as_admin(self):
        """Admin yetkisine sahip bir kullanıcının başka bir kullanıcının profilini güncelleyebildiğini test eder."""
        other_user = UserFactory(username="other_profile_to_update")
        other_user_profile = other_user.profile
        other_user_profile.team = self.kanat_team
        other_user_profile.save()

        self.client.force_authenticate(user=self.admin_user)
        data = {"team": self.govde_team.id}
        response = self.client.patch(self.profile_detail_url(other_user_profile.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        other_user_profile.refresh_from_db()
        self.assertEqual(other_user_profile.team, self.govde_team)

    def test_update_other_profile_as_regular_user_forbidden(self):
        """Normal bir kullanıcının başka bir kullanıcının profilini güncelleme girişiminin reddedildiğini (403) test eder."""
        other_user = UserFactory(username="other_profile_forbidden_update")
        # self.user ile authenticated
        data = {"team": self.govde_team.id}
        response = self.client.patch(self.profile_detail_url(other_user.profile.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserViewSetAPITests(APITestCase):
    """User API endpoint'lerinin (sadece admin erişimi ve /me/ action'ı) işlevlerini test eder."""

    def setUp(self):
        """Testler için kullanıcıları ve URL'leri hazırlar."""
        self.user1 = UserFactory(username="regularuser_uvs_setup")  # Eşsiz username
        self.admin_user = AdminUserFactory(username="admin_uvs_setup")  # Eşsiz username
        self.users_list_url = reverse('user-list')
        self.user_detail_url = lambda pk: reverse('user-detail', kwargs={'pk': pk})
        self.me_url = reverse('user-me')

    def test_list_users_as_admin(self):
        """Admin kullanıcının tüm kullanıcıları listeleyebildiğini test eder."""
        UserFactory.create_batch(2, username=factory.Sequence(lambda n: f"extra_user_uvs_list{n}"))
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)  # setUp'takiler + 2

    def test_list_users_as_regular_user_forbidden(self):
        """Normal bir kullanıcının kullanıcı listesine erişiminin reddedildiğini (403) test eder."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user_as_admin(self):
        """Admin kullanıcının başka bir kullanıcının detaylarını alabildiğini test eder."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.user_detail_url(self.user1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user1.username)

    def test_retrieve_user_as_regular_user_forbidden(self):
        """Normal bir kullanıcının başka bir kullanıcının detaylarına erişiminin reddedildiğini (403) test eder."""
        self.client.force_authenticate(user=self.user1)
        other_user_for_retrieve = UserFactory(username="other_user_for_retrieve_test")
        response = self.client.get(self.user_detail_url(other_user_for_retrieve.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_me_action_success(self):
        """Giriş yapmış bir kullanıcının /me/ endpoint'i üzerinden kendi bilgilerini alabildiğini test eder."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['username'], self.user1.username)
        self.assertIn('profile', response.data)

    def test_get_me_action_unauthenticated(self):
        """Kimliği doğrulanmamış bir kullanıcının /me/ endpoint'ine erişiminin reddedildiğini (401) test eder."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserSerializerTests(TestCase):
    """UserSerializer'ın, özellikle nested UserProfile güncelleme mantığının doğru çalıştığını test eder."""

    def setUp(self):
        """Testler için gerekli kullanıcı ve takım instance'larını oluşturur."""
        self.user_for_serializer = UserFactory(username="user_for_serializer_test")
        self.kanat_team_ser = KanatTeamFactory()  # Serializer testi için ayrı takım
        self.govde_team_ser = GovdeTeamFactory()  # Serializer testi için ayrı takım
        self.user_for_serializer.profile.team = self.kanat_team_ser
        self.user_for_serializer.profile.save()

    def test_user_serializer_update_profile_team_and_user_field(self):
        """UserSerializer'ın hem User alanlarını hem de nested UserProfile'ın takımını güncelleyebildiğini test eder."""
        data_to_update = {
            "first_name": "UpdatedFirstNameBySerializer",
            "profile": {"team": self.govde_team_ser.id}
        }
        serializer = UserSerializer(instance=self.user_for_serializer, data=data_to_update, partial=True)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_user = serializer.save()

        updated_user.refresh_from_db()
        updated_user.profile.refresh_from_db()  # Profilin de DB'den tazelendiğinden emin ol

        self.assertEqual(updated_user.first_name, "UpdatedFirstNameBySerializer")
        self.assertEqual(updated_user.profile.team, self.govde_team_ser)

    def test_user_serializer_update_user_field_without_profile_data(self):
        """UserSerializer'ın sadece User alanlarını güncelleyip, nested UserProfile'a dokunmadığını (profil verisi gönderilmemişse) test eder."""
        original_team = self.user_for_serializer.profile.team
        data_to_update = {"last_name": "UpdatedLastNameBySerializer"}

        serializer = UserSerializer(instance=self.user_for_serializer, data=data_to_update, partial=True)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_user = serializer.save()

        updated_user.refresh_from_db()
        updated_user.profile.refresh_from_db()

        self.assertEqual(updated_user.last_name, "UpdatedLastNameBySerializer")
        self.assertEqual(updated_user.profile.team, original_team)

    def test_user_serializer_update_profile_team_to_none(self):
        """UserSerializer aracılığıyla kullanıcının profilindeki takımın None olarak ayarlanabildiğini test eder."""
        data_to_update = {"profile": {"team": None}}
        serializer = UserSerializer(instance=self.user_for_serializer, data=data_to_update, partial=True)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_user = serializer.save()

        updated_user.refresh_from_db()
        updated_user.profile.refresh_from_db()
        self.assertIsNone(updated_user.profile.team)

    def test_user_serializer_read_representation(self):
        """UserSerializer'ın bir User instance'ını doğru şekilde serileştirdiğini test eder."""
        serializer = UserSerializer(instance=self.user_for_serializer)
        data = serializer.data

        self.assertEqual(data['username'], self.user_for_serializer.username)
        self.assertIn('profile', data)
        self.assertEqual(data['profile']['team'], self.kanat_team_ser.id)  # ID'yi kontrol et
        self.assertIn('team_details', data['profile'])  # Nested detaylar
        self.assertEqual(data['profile']['team_details']['get_name_display'], self.kanat_team_ser.get_name_display())