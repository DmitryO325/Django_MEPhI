# Generated by Django 5.1.3 on 2024-11-19 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='status',
            field=models.CharField(choices=[('DF', 'Draft'), ('P', 'Published')], default='DF', max_length=2),
        ),
    ]