from rest_framework import serializers

class TimeStampedSerializer(serializers.ModelSerializer):
    """
        created_at ve updated_at alanlarını içeren soyut bir base serializer.
        Bu alanlar salt okunurdur.
        """

    created_at = serializers.DateTimeField(
        read_only=True
    )
    updated_at = serializers.DateTimeField(
        read_only=True
    )
