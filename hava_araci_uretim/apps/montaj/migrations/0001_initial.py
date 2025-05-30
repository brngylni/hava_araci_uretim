# Generated by Django 5.2.1 on 2025-05-24 10:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('envanter', '0001_initial'),
        ('uretim', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssembledAircraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')),
                ('tail_number', models.CharField(max_length=50, unique=True, verbose_name='Kuyruk Numarası')),
                ('assembly_date', models.DateField(auto_now_add=True, verbose_name='Montaj Tarihi')),
                ('aircraft_model', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assembled_aircrafts', to='envanter.aircraftmodel', verbose_name='Uçak Modeli')),
                ('assembled_by_team', models.ForeignKey(limit_choices_to={'name': 'MONTAJ'}, null=True, on_delete=django.db.models.deletion.SET_NULL, to='uretim.team', verbose_name='Montajı Yapan Takım')),
                ('avionics', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='used_as_avionics_in', to='envanter.part', verbose_name='Aviyonik Parçası')),
                ('fuselage', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='used_as_fuselage_in', to='envanter.part', verbose_name='Gövde Parçası')),
                ('tail', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='used_as_tail_in', to='envanter.part', verbose_name='Kuyruk Parçası')),
                ('wing', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='used_as_wing_in', to='envanter.part', verbose_name='Kanat Parçası')),
            ],
            options={
                'verbose_name': 'Monte Edilmiş Uçak',
                'verbose_name_plural': 'Monte Edilmiş Uçaklar',
                'ordering': ['-assembly_date'],
            },
        ),
    ]
