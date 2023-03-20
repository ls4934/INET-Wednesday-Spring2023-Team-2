# Generated by Django 4.1.6 on 2023-03-20 06:35

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_alter_post_model_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='options_model',
            name='color',
            field=models.CharField(choices=[('C76B7F', 'C76B7F'), ('8CB369', '8CB369'), ('D7A5E4', 'D7A5E4'), ('5D6DD3', '5D6DD3')], default='c1', max_length=6),
        ),
        migrations.AlterField(
            model_name='post_model',
            name='category',
            field=multiselectfield.db.fields.MultiSelectField(choices=[('sports', 'Sports'), ('fantasy', 'Fantasy'), ('entertainment', 'Entertainment'), ('misc', 'Misc')], default='misc', max_length=20),
        ),
    ]
