# Generated by Django 5.1.5 on 2025-01-31 00:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('nisit', models.CharField(blank=True, max_length=11, unique=True)),
                ('degree', models.CharField(max_length=100)),
                ('seat', models.IntegerField(blank=True, unique=True)),
                ('verified', models.IntegerField(blank=True, default=0)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('rfid', models.CharField(blank=True, max_length=15, unique=True)),
            ],
        ),
    ]
