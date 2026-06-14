from django.db import migrations


def seed_object_classes(apps, schema_editor):
    ObjectClass = apps.get_model('datasets', 'ObjectClass')
    seeds = [
        {
            'name': 'class_01',
            'display_name': 'class_01',
            'description': 'Initial MVP object class.',
            'color': '#2563eb',
            'sort_order': 10,
        },
        {
            'name': 'class_02',
            'display_name': 'class_02',
            'description': 'Initial MVP object class.',
            'color': '#16a34a',
            'sort_order': 20,
        },
        {
            'name': 'other',
            'display_name': 'other',
            'description': 'Negative or non-target object class for reducing false positives.',
            'color': '#f97316',
            'sort_order': 30,
        },
    ]
    for seed in seeds:
        ObjectClass.objects.update_or_create(
            name=seed['name'],
            defaults=seed,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_object_classes, migrations.RunPython.noop),
    ]
