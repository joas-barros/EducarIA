from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_lotegeracaoquestao_questao'),
    ]

    operations = [
        migrations.RenameField(
            model_name='lotegeracaoquestao',
            old_name='quantidade_solicitada',
            new_name='quantidade_recebida',
        ),
        migrations.RemoveField(
            model_name='lotegeracaoquestao',
            name='parametros',
        ),
    ]
