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
