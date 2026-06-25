# Generated manually for feature questoes.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_ementa'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoteGeracaoQuestao',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantidade_solicitada', models.PositiveSmallIntegerField()),
                ('parametros', models.JSONField(blank=True, default=dict)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('disciplina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lotes_questoes', to='app.disciplina')),
                ('ementa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lotes_questoes', to='app.ementa')),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lotes_questoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Lote de geração de questões',
                'verbose_name_plural': 'Lotes de geração de questões',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='Questao',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[('multipla_escolha', 'Múltipla escolha'), ('verdadeiro_falso', 'Verdadeiro/Falso'), ('dissertativa', 'Dissertativa'), ('lacunas', 'Lacunas')], max_length=20)),
                ('enunciado', models.TextField()),
                ('dificuldade', models.CharField(choices=[('facil', 'Fácil'), ('medio', 'Médio'), ('dificil', 'Difícil')], max_length=10)),
                ('status', models.CharField(choices=[('gerada', 'Gerada'), ('aprovada', 'Aprovada'), ('editada', 'Editada')], default='gerada', max_length=10)),
                ('origem', models.CharField(choices=[('ia', 'IA'), ('manual', 'Manual')], default='ia', max_length=10)),
                ('ativa', models.BooleanField(default=True)),
                ('dados', models.JSONField(default=dict)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('disciplina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questoes', to='app.disciplina')),
                ('ementa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questoes', to='app.ementa')),
                ('lote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questoes', to='app.lotegeracaoquestao')),
            ],
            options={
                'verbose_name': 'Questão',
                'verbose_name_plural': 'Questões',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.AddIndex(
            model_name='lotegeracaoquestao',
            index=models.Index(fields=['professor', '-criado_em'], name='lote_q_prof_criado_idx'),
        ),
        migrations.AddIndex(
            model_name='lotegeracaoquestao',
            index=models.Index(fields=['disciplina', '-criado_em'], name='lote_q_disc_criado_idx'),
        ),
        migrations.AddIndex(
            model_name='questao',
            index=models.Index(fields=['disciplina', 'ativa', 'status', '-criado_em'], name='questao_disc_status_idx'),
        ),
        migrations.AddIndex(
            model_name='questao',
            index=models.Index(fields=['disciplina', 'tipo'], name='questao_disc_tipo_idx'),
        ),
        migrations.AddIndex(
            model_name='questao',
            index=models.Index(fields=['disciplina', 'dificuldade'], name='questao_disc_dific_idx'),
        ),
        migrations.AddIndex(
            model_name='questao',
            index=models.Index(fields=['ementa'], name='questao_ementa_idx'),
        ),
        migrations.AddIndex(
            model_name='questao',
            index=models.Index(fields=['lote'], name='questao_lote_idx'),
        ),
    ]
