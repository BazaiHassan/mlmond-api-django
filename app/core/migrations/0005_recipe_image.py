# Generated by Django 3.2.18 on 2023-02-16 07:29

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20230214_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='image',
            field=models.ImageField(null=True, upload_to=core.models.dataset_image_file_path),
        ),
    ]
