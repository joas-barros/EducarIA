from django import forms
from django.contrib.auth import get_user_model

Professor = get_user_model()

DIFICULDADE_IA_CHOICES = [
    ('mix', 'Mix balanceado (padrão)'),
    ('facil', 'Fácil'),
    ('medio', 'Médio'),
    ('dificil', 'Difícil'),
]

TIPO_QUESTAO_CHOICES = [
    ('multipla_escolha', 'Múltipla escolha'),
    ('dissertativa', 'Dissertativa'),
    ('verdadeiro_falso', 'Verdadeiro ou Falso'),
    ('lacunas', 'Completar lacunas'),
]

NIVEL_DISCIPLINA_CHOICES = [
    ('', 'Selecione...'),
    ('ensino_medio', 'Ensino Médio'),
    ('fundamental', 'Ensino Fundamental'),
    ('superior', 'Superior'),
]

TURNO_DISCIPLINA_CHOICES = [
    ('', 'Selecione...'),
    ('matutino', 'Matutino'),
    ('vespertino', 'Vespertino'),
    ('noturno', 'Noturno'),
]

DISCIPLINA_CHOICES = [
    ('', 'Selecione...'),
    ('Matemática', 'Matemática'),
    ('Inglês', 'Inglês'),
    ('Português', 'Português'),
    ('Espanhol', 'Espanhol'),
    ('Outra', 'Outra'),
]

NIVEL_CHOICES = [
    ('', 'Selecione...'),
    ('ensino_medio', 'Ensino Médio'),
    ('fundamental', 'Ensino Fundamental'),
    ('superior', 'Superior'),
]


class CadastroStep1Form(forms.Form):
    nome = forms.CharField(max_length=100, label='Nome')
    sobrenome = forms.CharField(max_length=100, label='Sobrenome')
    email = forms.EmailField(label='E-mail institucional')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Professor.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email


class CadastroStep2Form(forms.Form):
    disciplina_principal = forms.ChoiceField(
        choices=DISCIPLINA_CHOICES,
        label='Disciplina principal',
    )
    nivel_ensino = forms.ChoiceField(
        choices=NIVEL_CHOICES,
        label='Nível de ensino',
    )
    trabalha_com_idiomas = forms.BooleanField(
        required=False,
        label='Você trabalha com idiomas?',
    )


class CadastroStep3Form(forms.Form):
    senha = forms.CharField(
        widget=forms.PasswordInput,
        label='Senha',
        min_length=8,
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirmar senha',
    )
    aceite_lgpd = forms.BooleanField(
        label='Li e aceito os Termos de Uso e a Política de Privacidade (LGPD)',
    )
    aceite_email = forms.BooleanField(
        required=False,
        label='Quero receber dicas pedagógicas e novidades por e-mail',
    )

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        confirmar = cleaned.get('confirmar_senha')
        if senha and confirmar and senha != confirmar:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(label='E-mail institucional')
    senha = forms.CharField(widget=forms.PasswordInput, label='Senha')


EXTENSOES_ACEITAS = {'.pdf', '.docx', '.txt'}
TAMANHO_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


class EmentaForm(forms.Form):
    titulo = forms.CharField(
        max_length=200,
        label='Título',
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Ementa 2026 — 1º semestre'}),
    )
    descricao = forms.CharField(
        max_length=500,
        required=False,
        label='Descrição (opcional)',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Resumo breve do conteúdo...'}),
    )
    arquivo = forms.FileField(
        required=False,
        label='Arquivo (PDF, DOCX, TXT — máx. 10 MB)',
    )
    texto_colado = forms.CharField(
        required=False,
        label='Ou cole o texto da ementa',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Cole aqui o conteúdo da ementa...',
        }),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if not arquivo:
            return arquivo
        nome = arquivo.name.lower()
        ext = '.' + nome.rsplit('.', 1)[-1] if '.' in nome else ''
        if ext not in EXTENSOES_ACEITAS:
            raise forms.ValidationError('Formato não suportado. Use PDF, DOCX ou TXT.')
        if arquivo.size > TAMANHO_MAX_BYTES:
            raise forms.ValidationError('Arquivo muito grande. Máximo permitido: 10 MB.')
        return arquivo

    def clean(self):
        cleaned = super().clean()
        arquivo = cleaned.get('arquivo')
        texto = (cleaned.get('texto_colado') or '').strip()
        if not arquivo and not texto:
            raise forms.ValidationError(
                'É necessário enviar um arquivo ou colar o texto da ementa.'
            )
        if arquivo and texto:
            raise forms.ValidationError(
                'Envie apenas um arquivo OU cole o texto — não os dois ao mesmo tempo.'
            )
        return cleaned


class DisciplinaStep1Form(forms.Form):
    nome = forms.CharField(
        max_length=200,
        label='Nome da disciplina',
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Inglês 3º ano A'}),
    )
    nivel = forms.ChoiceField(choices=NIVEL_DISCIPLINA_CHOICES, label='Nível de ensino')
    serie_ano = forms.CharField(
        max_length=20, required=False, label='Série / Ano',
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 3º ano'}),
    )
    turno = forms.ChoiceField(choices=TURNO_DISCIPLINA_CHOICES, required=False, label='Turno')
    num_alunos_estimado = forms.IntegerField(
        required=False, min_value=1, label='Nº estimado de alunos',
        widget=forms.NumberInput(attrs={'placeholder': 'Ex: 32'}),
    )
    periodo_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Início do período',
    )
    periodo_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fim do período',
    )


class DisciplinaStep2Form(forms.Form):
    dificuldade_padrao = forms.ChoiceField(
        choices=DIFICULDADE_IA_CHOICES, required=False, initial='mix',
        label='Dificuldade padrão das questões',
    )
    tipos_preferidos = forms.MultipleChoiceField(
        choices=TIPO_QUESTAO_CHOICES, required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Tipos de questão preferidos',
    )
    observacoes_ia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Ex: focar em interpretação de texto, evitar questões muito teóricas...',
        }),
        label='Observações para a IA (opcional)',
    )


class DisciplinaEditForm(forms.Form):
    nome = forms.CharField(max_length=200, label='Nome da disciplina')
    nivel = forms.ChoiceField(choices=NIVEL_DISCIPLINA_CHOICES, label='Nível de ensino')
    serie_ano = forms.CharField(max_length=20, required=False, label='Série / Ano')
    turno = forms.ChoiceField(choices=TURNO_DISCIPLINA_CHOICES, required=False, label='Turno')
    num_alunos_estimado = forms.IntegerField(
        required=False, min_value=1, label='Nº estimado de alunos',
    )
    periodo_inicio = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='Início do período',
    )
    periodo_fim = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='Fim do período',
    )
    dificuldade_padrao = forms.ChoiceField(
        choices=DIFICULDADE_IA_CHOICES, required=False, label='Dificuldade padrão das questões',
    )
    tipos_preferidos = forms.MultipleChoiceField(
        choices=TIPO_QUESTAO_CHOICES, required=False,
        widget=forms.CheckboxSelectMultiple, label='Tipos de questão preferidos',
    )
    observacoes_ia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Observações para a IA (opcional)',
    )
