from django.db import migrations


def create_categories(apps, schema_editor):
    Category = apps.get_model('expenses', 'Category')
    Category.objects.bulk_create([
        Category(name=name) for name in (
            'Food',
            'Transport',
            'Shopping',
            'Bills',
            'Entertainment',
            'Other',
        )
    ])


def remove_categories(apps, schema_editor):
    Category = apps.get_model('expenses', 'Category')
    Category.objects.filter(name__in=(
        'Food', 'Transport', 'Shopping', 'Bills', 'Entertainment', 'Other'
    )).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_categories, remove_categories),
    ]