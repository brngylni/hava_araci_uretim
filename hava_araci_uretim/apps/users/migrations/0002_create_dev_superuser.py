from django.db import migrations


def create_development_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    DEV_SUPERUSER_USERNAME = 'root'
    DEV_SUPERUSER_EMAIL = 'admin_dev@example.com'
    DEV_SUPERUSER_PASSWORD = 'root123'  # Basit bir şifre, sadece geliştirme için

    # Eğer bu kullanıcı zaten varsa oluşturma
    if not User.objects.filter(username=DEV_SUPERUSER_USERNAME).exists():
        User.objects.create_superuser(
            username=DEV_SUPERUSER_USERNAME,
            email=DEV_SUPERUSER_EMAIL,
            password=DEV_SUPERUSER_PASSWORD
        )
        print(f"\nGeliştirme süper kullanıcısı '{DEV_SUPERUSER_USERNAME}' oluşturuldu.")
        print(f"Şifre: {DEV_SUPERUSER_PASSWORD} (Lütfen ilk girişten sonra değiştirin!)")
    else:
        print(f"\nGeliştirme süper kullanıcısı '{DEV_SUPERUSER_USERNAME}' zaten mevcut.")


def remove_development_superuser(apps, schema_editor):

    User = apps.get_model('auth', 'User')
    DEV_SUPERUSER_USERNAME = 'admin_dev'
    try:
        user = User.objects.get(username=DEV_SUPERUSER_USERNAME)
        if user.is_superuser:  # Sadece gerçekten bu migration'ın oluşturduğu ise sil
            user.delete()
            print(f"\nGeliştirme süper kullanıcısı '{DEV_SUPERUSER_USERNAME}' silindi.")
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [

        ('users', '0001_initial'),

    ]
    operations = [
        migrations.RunPython(create_development_superuser, remove_development_superuser),
    ]