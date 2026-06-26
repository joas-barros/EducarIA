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
        self.questoes.update(ativa=False)
        # Quando Listening/Flashcard existirem, inativar aqui também.


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

    @property
    def possui_infografico(self):
        return hasattr(self, 'infografico') and self.infografico is not None


def infografico_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    return f'infograficos/{instance.ementa.disciplina_id}/{instance.ementa_id}/{instance.id}.{ext}'


class Infografico(models.Model):
    STATUS_PENDENTE = 'pendente'
    STATUS_GERADO = 'gerado'
    STATUS_ERRO = 'erro'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_GERADO, 'Gerado'),
        (STATUS_ERRO, 'Erro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ementa = models.OneToOneField(
        Ementa,
        on_delete=models.CASCADE,
        related_name='infografico',
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='infograficos',
    )
    arquivo = models.FileField(upload_to=infografico_upload_path, blank=True, null=True)
    texto_resumo = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Infográfico'
        verbose_name_plural = 'Infográficos'

    def __str__(self):
        return f'Infográfico de {self.ementa.titulo}'


class QuestaoQuerySet(models.QuerySet):
    def ativas(self):
        return self.filter(ativa=True, disciplina__excluida_em__isnull=True)

    def banco(self):
        return self.ativas().filter(status__in=[
            Questao.STATUS_APROVADA,
            Questao.STATUS_EDITADA,
        ])

    def geradas(self):
        return self.ativas().filter(status=Questao.STATUS_GERADA)

    def do_professor(self, professor):
        return self.filter(disciplina__professor=professor)


class LoteGeracaoQuestao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lotes_questoes',
    )
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name='lotes_questoes',
    )
    ementa = models.ForeignKey(
        Ementa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lotes_questoes',
    )
    quantidade_recebida = models.PositiveSmallIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Lote de geração de questões'
        verbose_name_plural = 'Lotes de geração de questões'
        indexes = [
            models.Index(fields=['professor', '-criado_em'], name='lote_q_prof_criado_idx'),
            models.Index(fields=['disciplina', '-criado_em'], name='lote_q_disc_criado_idx'),
        ]

    def __str__(self):
        return f'{self.disciplina.nome} — {self.criado_em:%d/%m/%Y %H:%M}'


class Questao(models.Model):
    TIPO_MULTIPLA_ESCOLHA = 'multipla_escolha'
    TIPO_VERDADEIRO_FALSO = 'verdadeiro_falso'
    TIPO_DISSERTATIVA = 'dissertativa'
    TIPO_LACUNAS = 'lacunas'

    TIPO_CHOICES = [
        (TIPO_MULTIPLA_ESCOLHA, 'Múltipla escolha'),
        (TIPO_VERDADEIRO_FALSO, 'Verdadeiro/Falso'),
        (TIPO_DISSERTATIVA, 'Dissertativa'),
        (TIPO_LACUNAS, 'Lacunas'),
    ]

    DIFICULDADE_FACIL = 'facil'
    DIFICULDADE_MEDIO = 'medio'
    DIFICULDADE_DIFICIL = 'dificil'

    DIFICULDADE_CHOICES = [
        (DIFICULDADE_FACIL, 'Fácil'),
        (DIFICULDADE_MEDIO, 'Médio'),
        (DIFICULDADE_DIFICIL, 'Difícil'),
    ]

    STATUS_GERADA = 'gerada'
    STATUS_APROVADA = 'aprovada'
    STATUS_EDITADA = 'editada'

    STATUS_CHOICES = [
        (STATUS_GERADA, 'Gerada'),
        (STATUS_APROVADA, 'Aprovada'),
        (STATUS_EDITADA, 'Editada'),
    ]

    ORIGEM_IA = 'ia'
    ORIGEM_MANUAL = 'manual'

    ORIGEM_CHOICES = [
        (ORIGEM_IA, 'IA'),
        (ORIGEM_MANUAL, 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name='questoes',
    )
    ementa = models.ForeignKey(
        Ementa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questoes',
    )
    lote = models.ForeignKey(
        LoteGeracaoQuestao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questoes',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    enunciado = models.TextField()
    dificuldade = models.CharField(max_length=10, choices=DIFICULDADE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_GERADA)
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default=ORIGEM_IA)
    ativa = models.BooleanField(default=True)
    dados = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = QuestaoQuerySet.as_manager()

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Questão'
        verbose_name_plural = 'Questões'
        indexes = [
            models.Index(fields=['disciplina', 'ativa', 'status', '-criado_em'], name='questao_disc_status_idx'),
            models.Index(fields=['disciplina', 'tipo'], name='questao_disc_tipo_idx'),
            models.Index(fields=['disciplina', 'dificuldade'], name='questao_disc_dific_idx'),
            models.Index(fields=['ementa'], name='questao_ementa_idx'),
            models.Index(fields=['lote'], name='questao_lote_idx'),
        ]

    def __str__(self):
        return self.enunciado[:80]


class Prova(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=200)
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provas',
    )
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name='provas',
    )
    questoes = models.ManyToManyField(
        Questao,
        related_name='provas',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Prova'
        verbose_name_plural = 'Provas'

    def __str__(self):
        return self.titulo
