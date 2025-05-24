import factory
from django.contrib.auth.models import User

from apps.uretim.factories import TeamFactory
from apps.users.models import UserProfile


class UserFactory(factory.django.DjangoModelFactory):
    """
    Django User objeleri için fabrika.
    Otomatik olarak username, email, first_name, last_name ve password (hash'lenmiş) atar.
    UserProfile objesinin Django sinyali ile otomatik oluşturulduğunu varsayar.
    """

    class Meta:
        model = User
        django_get_or_create = ('username',)


    username = factory.Sequence(lambda n: f"testuser{n}")  # Eşsiz username.
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")  # username'e bağlı email.
    first_name = factory.Faker('first_name')  # Rastgele gerçekçi isim. Güzel.
    last_name = factory.Faker('last_name')  # Rastgele gerçekçi soyisim. Güzel.
    is_staff = False  # Varsayılan.
    is_superuser = False  # Varsayılan.

    # Post-generation hook (Şifre ayarlamak için):
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """
        User objesi oluşturulduktan sonra şifresini ayarlar ve kaydeder.
        Eğer factory çağrılırken `password="my_pass"` gibi bir değer verilirse onu kullanır,
        aksi takdirde varsayılan bir şifre ('defaultpassword123') kullanır.
        """

        pw_to_set = 'defaultpassword123'
        if extracted:
            pw_to_set = extracted

        obj.set_password(pw_to_set)  # Şifreyi hashle

        if create:  # Ek Kontrol
            obj.save(update_fields=['password'])


class AdminUserFactory(UserFactory):
    """
    Admin yetkilerine (is_staff=True, is_superuser=True) sahip User objeleri için fabrika.
    UserFactory'den miras alır.
    """

    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f"adminuser{n}")

class UserProfileFactory(factory.django.DjangoModelFactory):
    """
    UserProfile objeleri için fabrika.
    Otomatik olarak bir User objesi (UserFactory aracılığıyla) ve
    bir Team objesi (TeamFactory aracılığıyla) oluşturup ilişkilendirir.
    DİKKAT: User oluşturulduğunda Django sinyali de bir UserProfile oluşturur.
    Bu factory doğrudan kullanıldığında, sinyalin oluşturduğu profille çakışmaması için
    Meta.django_get_or_create = ('user',) ayarı önemlidir.
    """

    class Meta:
        model = UserProfile
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory) # Varsayılan olarak üretim takımı