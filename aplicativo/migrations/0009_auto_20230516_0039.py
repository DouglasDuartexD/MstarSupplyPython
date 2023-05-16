# Generated by Django 3.2 on 2023-05-16 03:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('aplicativo', '0008_movimentacao_deletado'),
    ]

    operations = [
        migrations.RenameField(
            model_name='movimentacao',
            old_name='tipomovimentacao',
            new_name='tipo_movimentacao',
        ),
        migrations.RemoveField(
            model_name='movimentacao',
            name='datahora',
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='data_hora',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
