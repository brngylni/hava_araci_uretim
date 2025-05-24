from django.db import migrations

INITIAL_PART_TYPES = [
    {'name': 'KANAT'},
    {'name': 'GOVDE'},
    {'name': 'KUYRUK'},
    {'name': 'AVIYONIK'},
]

def create_initial_part_types(apps, schema_editor):
    print("CREATING PART TYPES")
    PartType = apps.get_model('envanter', 'PartType')
    for pt_data in INITIAL_PART_TYPES:
        PartType.objects.get_or_create(name=pt_data['name'])
    print("CREATED PART TYPES")

def remove_initial_part_types(apps, schema_editor):

    PartType = apps.get_model('envanter', 'PartType')
    for pt_data in INITIAL_PART_TYPES:
        try:
            part_type_instance = PartType.objects.get(name=pt_data['name'])
            part_type_instance.delete()
        except PartType.DoesNotExist:
            pass

class Migration(migrations.Migration):

    dependencies = [

        ('envanter', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_part_types, remove_initial_part_types),
    ]