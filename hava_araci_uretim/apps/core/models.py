from django.db import models

class TimeStampedModel(models.Model):
    """
    Zaman damgalarını (oluşturulma ve güncellenme) tutan bir abstract base model.
    """
    created_at = models.DateTimeField(
        auto_now_add=True, # Obje oluşunca güncelle
        verbose_name="Oluşturulma Tarihi" # Admin panelinde görünecek isim.
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Güncellenme Tarihi"
    )

    class Meta:
        abstract = True # Soyut model. Sadece kalıtım için kullanılacak.

        ordering = ['-created_at', '-updated_at'] # Oluşturulma tarihine göre sırala