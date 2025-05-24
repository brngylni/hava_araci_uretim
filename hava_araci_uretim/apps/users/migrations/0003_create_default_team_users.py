from django.db import migrations

DEFAULT_TEAMS_INFO = [
    {'name': 'KANAT', 'is_production': True},
    {'name': 'GOVDE', 'is_production': True},
    {'name': 'KUYRUK', 'is_production': True},
    {'name': 'AVIYONIK', 'is_production': True},
    {'name': 'MONTAJ', 'is_production': False},
]


def create_default_users_for_teams(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('users', 'UserProfile')  # UserProfile modeliniz
    Team = apps.get_model('uretim', 'Team')  # Team modeliniz

    print("\nDEBUG: Varsayılan takım kullanıcıları oluşturuluyor...")

    for team_info in DEFAULT_TEAMS_INFO:
        team_code_name = team_info['name']  # Örn: KANAT, MONTAJ
        username = team_code_name.lower()  # Örn: kanat, montaj
        password = f"{username}123"  # Örn: kanat123, montaj123
        email = f"{username}@example.com"

        try:
            # İlgili takımı bul
            team_instance = Team.objects.get(name=team_code_name)

            # Kullanıcı zaten varsa dokunma
            if not User.objects.filter(username=username).exists():
                # User.objects.create_user şifreyi otomatik hash'ler.
                user_instance = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=team_instance.get_name_display(),
                    last_name="Kullanıcısı"
                )

                try:
                    profile = UserProfile.objects.get(user=user_instance)
                    profile.team = team_instance
                    profile.save(update_fields=['team'])
                    print(
                        f"  Kullanıcı '{username}' oluşturuldu ve '{team_instance.get_name_display()}' takımına atandı.")
                except UserProfile.DoesNotExist:

                    UserProfile.objects.create(user=user_instance, team=team_instance)
                    print(
                        f"  Kullanıcı '{username}' oluşturuldu, profili oluşturuldu ve '{team_instance.get_name_display()}' takımına atandı.")
            else:
                print(f"  Kullanıcı '{username}' zaten mevcut, takım ataması kontrol ediliyor...")
                user_instance = User.objects.get(username=username)
                if not hasattr(user_instance, 'profile'):
                    UserProfile.objects.create(user=user_instance, team=team_instance)
                    print(f"    '{username}' için profil oluşturuldu ve takım atandı.")
                elif user_instance.profile.team != team_instance:
                    user_instance.profile.team = team_instance
                    user_instance.profile.save(update_fields=['team'])
                    print(
                        f"    '{username}' kullanıcısı '{team_instance.get_name_display()}' takımına atandı (güncellendi).")


        except Team.DoesNotExist:
            print(f"UYARI: '{team_code_name}' adlı takım bulunamadı. Bu takım için kullanıcı oluşturulamadı.")
        except Exception as e:
            print(f"HATA: Kullanıcı '{username}' oluşturulurken/atanırken bir sorun oluştu: {e}")

    print("DEBUG: Varsayılan takım kullanıcıları oluşturma işlemi tamamlandı.\n")


def remove_default_team_users(apps, schema_editor):

    User = apps.get_model('auth', 'User')
    for team_info in DEFAULT_TEAMS_INFO:
        username = team_info['name'].lower()
        try:
            user = User.objects.get(username=username)

            if user.first_name.endswith("Takımı"):
                user.delete()
                print(f"Varsayılan takım kullanıcısı '{username}' silindi.")
        except User.DoesNotExist:
            pass


class Migration(migrations.Migration):
    dependencies = [

        ('users', '0002_create_dev_superuser'),  # UserProfile modelini oluşturan/son değiştiren
        ('uretim', '0002_populate_initial_teams'),  # Takımları oluşturan data migration

    ]

    operations = [
        migrations.RunPython(create_default_users_for_teams, remove_default_team_users),
    ]