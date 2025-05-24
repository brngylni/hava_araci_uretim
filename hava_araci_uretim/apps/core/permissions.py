# apps/core/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS
# SAFE_METHODS: ('GET', 'HEAD', 'OPTIONS') gibi okuma amaçlı HTTP metodlarını içerir.


class IsTeamMemberOrReadOnly(BasePermission):
    """
    Bu izin sınıfı, bir objeye yapılan isteğin HTTP metodu SAFE_METHODS içindeyse (GET, HEAD, OPTIONS gibi)
    herkese izin verir (okuma izni).
    Eğer metot SAFE_METHODS içinde değilse (POST, PUT, PATCH, DELETE gibi yazma/değiştirme işlemleri),
    sadece objeyle ilişkili takımın üyesi olan kullanıcılara izin verir.
    Bu sınıf, objenin 'produced_by_team', 'team' veya 'assembled_by_team' gibi bir ForeignKey
    alanına sahip olduğunu varsayar, bu alan üzerinden kullanıcının takımıyla karşılaştırma yapar.
    """
    message = "Bu objeyi sadece ilgili takım üyeleri değiştirebilir."  # Hata durumunda kullanıcıya gösterilecek mesaj.

    def has_object_permission(self, request, view, obj):
        # request: Mevcut HTTP isteği.
        # view: İsteği işleyen view.
        # obj: Üzerinde izin kontrolü yapılan model instance'ı.

        if request.method in SAFE_METHODS:
            return True

        # Kullanıcının bir profili ve bu profile bağlı bir takımı olmalı.
        # Eğer kullanıcı anonimse veya bir takıma atanmamışsa, yazma izni verilmez.
        if not hasattr(request.user, 'profile') or not request.user.profile.team:
            return False

        user_team = request.user.profile.team  # İstek yapan kullanıcının takımı.

        # Part
        if hasattr(obj, 'produced_by_team'):
            return obj.produced_by_team == user_team  # Parçayı üreten takım, kullanıcının takımı mı?

        # UserProfile
        elif hasattr(obj, 'team'):
            # Objenin takımı kullanıcının takımı mı?
            return obj.team == user_team

        #  AssembledAircraft
        elif hasattr(obj, 'assembled_by_team'):
            return obj.assembled_by_team == user_team  # Uçağı monte eden takım, kullanıcının takımı mı?

        return False


class IsProductionTeamAndResponsibleForPartType(BasePermission):
    """
    Bu izin sınıfı, kullanıcının bir üretim takımına ait olup olmadığını ve
    bu takımın, işlem yapılan parça tipi için sorumlu olup olmadığını kontrol eder.
    Özellikle parça üretimi ve yönetimi (güncelleme, geri dönüşüm) için kullanılır.
    """
    message = "Bu parça tipini üretme veya yönetme yetkiniz yok veya bir üretim takımında değilsiniz."

    def has_permission(self, request, view):
        # Kullanıcının bir profili ve bu profile bağlı bir takımı olmalı.
        if not hasattr(request.user, 'profile') or not request.user.profile.team:
            return False

        user_team = request.user.profile.team

        # Kullanıcının takımı bir üretim takımı olmalı (Montaj Takımı değil)
        # ve bu üretim takımının sorumlu olduğu bir parça tipi tanımlanmış olmalı.
        if user_team.name == 'MONTAJ' or not user_team.responsible_part_type:
            return False
        return True

    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True

        if not hasattr(request.user, 'profile') or not request.user.profile.team:
            return False

        user_team = request.user.profile.team

        if user_team.name == 'MONTAJ' or not user_team.responsible_part_type:
            return False  # Kullanıcı üretim takımında değil veya sorumlu olduğu tip yok.

        # 'obj' bir Part instance'ı olmalı.
        # Parçanın 'part_type' alanı, kullanıcının takımının 'responsible_part_type' alanı ile eşleşmeli.
        # VE parçanın 'produced_by_team' alanı, kullanıcının takımı ile eşleşmeli (bu parçayı kendi takımı üretmiş olmalı).
        if hasattr(obj, 'part_type') and hasattr(obj, 'produced_by_team'):
            return obj.produced_by_team == user_team and \
                user_team.responsible_part_type == obj.part_type

        # Eğer obje bir Part değilse veya gerekli alanlara sahip değilse, izin verme.
        return False


class IsAssemblyTeam(BasePermission):
    """
    Bu izin sınıfı, bir işlemi sadece "Montaj Takımı" üyelerinin yapabilmesini sağlar.
    Özellikle uçak montajı (create) ve monte edilmiş uçakların yönetimi (update, delete) için kullanılır.
    """
    message = "Bu işlemi sadece Montaj Takımı üyeleri yapabilir."

    def has_permission(self, request, view):
        # Kullanıcının bir profili ve takımı olmalı.
        if not hasattr(request.user, 'profile') or not request.user.profile.team:
            return False
        # Kullanıcının takımı "MONTAJ" takımı mı? Team modelindeki name alanı 'MONTAJ' olmalı.
        return request.user.profile.team.name == 'MONTAJ'

    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True

        # Yazma/değiştirme işlemleri için:
        # Kullanıcının bir profili ve takımı olmalı.
        if not hasattr(request.user, 'profile') or not request.user.profile.team:
            return False

        # Kullanıcının takımı "MONTAJ" takımı mı?
        # VE işlem yapılan 'obj' (AssembledAircraft instance'ı) bu takım tarafından mı monte edilmiş?

        return request.user.profile.team.name == 'MONTAJ'  # and obj.assembled_by_team == request.user.profile.team
        # Şimdilik, herhangi bir montaj takımı üyesi tüm monte edilmiş uçakları (kendi monte etmese bile) değiştirebilsin.


class CanRecyclePart(BasePermission):
    """
    Bu izin sınıfı, bir parçayı sadece onu üreten takımın geri dönüşüme gönderebilmesini sağlar.
    Part modelinin 'recycle' action'ı için kullanılır.
    """
    message = "Bu parçayı sadece üreten takım geri dönüşüme gönderebilir veya parça zaten geri dönüşümde."

    def has_object_permission(self, request, view, obj):
        # 'obj' bir Part instance'ı olmalı.
        # Kullanıcının bir profili ve takımı olmalı.
        if not hasattr(request.user, 'profile') or not request.user.profile.team:
            return False

        user_team = request.user.profile.team

        # Parçanın 'produced_by_team' alanı, istek yapan kullanıcının takımı ile aynı olmalı.
        # VE parçanın durumu 'GERI_DONUSUMDE' olmamalı (zaten geri dönüşümde olan bir şey tekrar gönderilemez).
        return hasattr(obj, 'produced_by_team') and \
            obj.produced_by_team == user_team and \
            obj.status != 'GERI_DONUSUMDE'