# Generated by Django 3.2 on 2023-05-13 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aplicativo', '0002_auto_20230513_1804'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='imagem',
            field=models.ImageField(blank=True, null=True, upload_to='imagens/'),
        ),
    ]
