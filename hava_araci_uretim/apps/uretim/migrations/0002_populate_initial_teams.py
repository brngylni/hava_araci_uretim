from django.db import migrations

TEAM_DEFINITIONS = [
    {'name': 'KANAT', 'is_production': True},
    {'name': 'GOVDE', 'is_production': True},
    {'name': 'KUYRUK', 'is_production': True},
    {'name': 'AVIYONIK', 'is_production': True},
    {'name': 'MONTAJ', 'is_production': False},
]

def create_initial_teams(apps, schema_editor):
    Team = apps.get_model('uretim', 'Team')
    PartType = apps.get_model('envanter', 'PartType')  # envanter.PartType'a erişim

    for team_def in TEAM_DEFINITIONS:
        team_name = team_def['name']
        is_production = team_def['is_production']

        responsible_part_type_instance = None
        if is_production:
            try:
                responsible_part_type_instance = PartType.objects.get(name=team_name)
            except PartType.DoesNotExist:
                print(f"UYARI (Team Migration): '{team_name}' adlı PartType bulunamadı. "
                      f"'{team_name}' takımı için responsible_part_type None olarak ayarlanacak.")

        team, created = Team.objects.get_or_create(
            name=team_name,
            defaults={'responsible_part_type': responsible_part_type_instance}
        )

        if not created and team.responsible_part_type != responsible_part_type_instance:

            team.responsible_part_type = responsible_part_type_instance
            team.save(update_fields=['responsible_part_type'])
        elif created:
            print(f"Takım oluşturuldu: {team_name} (Sorumlu Tip: {responsible_part_type_instance})")
        else:
            print(f"Takım zaten vardı: {team_name} (Sorumlu Tip: {team.responsible_part_type})")


def remove_initial_teams(apps, schema_editor):
    Team = apps.get_model('uretim', 'Team')
    for team_def in TEAM_DEFINITIONS:
        try:
            team_instance = Team.objects.get(name=team_def['name'])
            team_instance.delete()
            print(f"Takım silindi: {team_def['name']}")
        except Team.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('uretim', '0001_initial'),
        ('envanter', '0003_populate_initial_part_types'),
    ]

    operations = [
        migrations.RunPython(create_initial_teams, remove_initial_teams),
    ]