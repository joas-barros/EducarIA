# Gerado manualmente — Sprint 3: Módulo Listening

import app.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_ementa'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExercicioListening',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('idioma', models.CharField(
                    choices=[('en', 'Inglês'), ('es', 'Espanhol')],
                    default='en', max_length=5,
                )),
                ('nivel', models.CharField(
                    choices=[('A2', 'Iniciante (A2)'), ('B1', 'Intermediário (B1)'), ('B2', 'Avançado (B2)')],
                    default='B1', max_length=5,
                )),
                ('voz', models.CharField(
                    choices=[
                        ('en-US-Neural2-F', 'Emma – americana, feminina'),
                        ('en-US-Neural2-D', 'James – americano, masculino'),
                        ('en-GB-Neural2-A', 'Olivia – britânica, feminina'),
                        ('es-US-Neural2-A', 'Sofia – hispânica, feminina'),
                        ('es-US-Neural2-B', 'Carlos – hispânico, masculino'),
                    ],
                    default='en-US-Neural2-F', max_length=30,
                )),
                ('tema_livre', models.CharField(blank=True, max_length=300)),
                ('roteiro', models.TextField()),
                ('audio', models.FileField(
                    blank=True, null=True,
                    upload_to=app.models.listening_audio_path,
                )),
                ('audio_duracao_segundos', models.PositiveIntegerField(blank=True, null=True)),
                ('gerado_por_ia', models.BooleanField(default=True)),
                ('ativa', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('disciplina', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='exercicios_listening',
                    to='app.disciplina',
                )),
                ('ementa', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='exercicios_listening',
                    to='app.ementa',
                )),
            ],
            options={
                'verbose_name': 'Exercício de Listening',
                'verbose_name_plural': 'Exercícios de Listening',
                'ordering': ['-criado_em'],
            },
        ),
    ]
