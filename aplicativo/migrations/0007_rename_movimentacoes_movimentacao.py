# Generated by Django 3.2 on 2023-05-14 16:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aplicativo', '0006_produto_descricao'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Movimentacoes',
            new_name='Movimentacao',
        ),
    ]
