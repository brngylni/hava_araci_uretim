from django.db import migrations

INITIAL_AIRCRAFT_MODELS = [
    {'name': 'TB2'},
    {'name': 'TB3'},
    {'name': 'AKINCI'},
    {'name': 'KIZILELMA'},
]

def create_initial_aircraft_models(apps, schema_editor):

    AircraftModel = apps.get_model('envanter', 'AircraftModel')
    for pt_data in INITIAL_AIRCRAFT_MODELS:
        AircraftModel.objects.get_or_create(name=pt_data['name'])


def remove_initial_aircraft_models(apps, schema_editor):

    AircraftModel = apps.get_model('envanter', 'AircraftModel')
    for pt_data in INITIAL_AIRCRAFT_MODELS:
        try:
            aircraft_model_instance = AircraftModel.objects.get(name=pt_data['name'])
            aircraft_model_instance.delete()
        except AircraftModel.DoesNotExist:
            pass

class Migration(migrations.Migration):

    dependencies = [

        ('envanter', '0003_populate_initial_part_types'),
    ]

    operations = [
        migrations.RunPython(create_initial_aircraft_models, remove_initial_aircraft_models),
    ]