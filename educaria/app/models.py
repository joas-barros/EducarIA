import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Professor(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    trabalha_com_idiomas = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'

    def __str__(self):
        return self.get_full_name() or self.email


class DisciplinaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(excluida_em__isnull=True)


class Disciplina(models.Model):
    NIVEL_CHOICES = [
        ('ensino_medio', 'Ensino Médio'),
        ('fundamental', 'Ensino Fundamental'),
        ('superior', 'Superior'),
    ]
    TURNO_CHOICES = [
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('noturno', 'Noturno'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disciplinas',
    )
    nome = models.CharField(max_length=200)
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    serie_ano = models.CharField(max_length=20, blank=True)
    turno = models.CharField(max_length=15, choices=TURNO_CHOICES, blank=True)
    num_alunos_estimado = models.PositiveIntegerField(null=True, blank=True)
    periodo_inicio = models.DateField(null=True, blank=True)
    periodo_fim = models.DateField(null=True, blank=True)
    config_ia = models.JSONField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    excluida_em = models.DateTimeField(null=True, blank=True)

    objects = DisciplinaManager()
    todos = models.Manager()

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        return self.nome

    def soft_delete(self):
        self.excluida_em = timezone.now()
        self.save(update_fields=['excluida_em'])
        # Quando Questao/Listening/Flashcard existirem, inativar aqui


def ementa_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    return f'ementas/{instance.disciplina_id}/{instance.id}.{ext}'


class Ementa(models.Model):
    TIPO_FONTE_CHOICES = [
        ('arquivo', 'Arquivo'),
        ('texto_colado', 'Texto colado'),
    ]
    ARQUIVO_TIPO_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('txt', 'TXT'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name='ementas',
    )
    titulo = models.CharField(max_length=200)
    descricao = models.CharField(max_length=500, blank=True)
    tipo_fonte = models.CharField(max_length=15, choices=TIPO_FONTE_CHOICES)
    arquivo = models.FileField(upload_to=ementa_upload_path, blank=True, null=True)
    arquivo_nome = models.CharField(max_length=255, blank=True)
    arquivo_tipo = models.CharField(max_length=5, choices=ARQUIVO_TIPO_CHOICES, blank=True)
    arquivo_tamanho_bytes = models.PositiveIntegerField(null=True, blank=True)
    texto_colado = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Ementa'
        verbose_name_plural = 'Ementas'

    def __str__(self):
        return self.titulo

    @property
    def tamanho_legivel(self):
        if not self.arquivo_tamanho_bytes:
            return ''
        kb = self.arquivo_tamanho_bytes / 1024
        if kb < 1024:
            return f'{kb:.0f} KB'
        return f'{kb / 1024:.1f} MB'
