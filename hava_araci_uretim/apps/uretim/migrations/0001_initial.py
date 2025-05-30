# Generated by Django 5.2.1 on 2025-05-24 10:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('envanter', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')),
                ('name', models.CharField(choices=[('KANAT', 'Kanat Takımı'), ('GOVDE', 'Gövde Takımı'), ('KUYRUK', 'Kuyruk Takımı'), ('AVIYONIK', 'Aviyonik Takımı'), ('MONTAJ', 'Montaj Takımı')], max_length=100, unique=True, verbose_name='Takım Adı')),
                ('responsible_part_type', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='responsible_team', to='envanter.parttype', verbose_name='Sorumlu Olduğu Parça Tipi')),
            ],
            options={
                'verbose_name': 'Takım',
                'verbose_name_plural': 'Takımlar',
                'ordering': ['name'],
            },
        ),
    ]
