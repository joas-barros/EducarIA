import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Disciplina, Ementa, Questao, Prova
from .services.questoes import validar_dados_questao

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


class QuestaoBaseForm(forms.Form):
    campos_dados = []

    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.none(),
        label='Disciplina',
        widget=forms.Select(attrs={'class': 'sel'}),
    )
    ementa = forms.ModelChoiceField(
        queryset=Ementa.objects.none(),
        required=False,
        label='Ementa de origem (opcional)',
        widget=forms.Select(attrs={'class': 'sel'}),
    )
    tipo = forms.ChoiceField(
        choices=Questao.TIPO_CHOICES,
        label='Tipo',
        widget=forms.Select(attrs={'class': 'sel', 'data-role': 'tipo-selector'}),
    )
    dificuldade = forms.ChoiceField(
        choices=Questao.DIFICULDADE_CHOICES,
        label='Dificuldade',
        widget=forms.Select(attrs={'class': 'sel'}),
    )
    enunciado = forms.CharField(
        label='Enunciado',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 4}),
    )

    def __init__(self, *args, professor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.professor = professor
        if professor is not None:
            self.fields['disciplina'].queryset = Disciplina.objects.filter(professor=professor)
            self.fields['ementa'].queryset = Ementa.objects.filter(disciplina__professor=professor)

    def clean(self):
        cleaned = super().clean()
        disciplina = cleaned.get('disciplina')
        ementa = cleaned.get('ementa')
        tipo = cleaned.get('tipo')

        if disciplina and ementa and ementa.disciplina_id != disciplina.id:
            self.add_error('ementa', 'Ementa não pertence à disciplina selecionada.')

        if tipo and not any(self.errors.get(campo) for campo in self.campos_dados):
            try:
                validar_dados_questao(tipo, self.montar_dados())
            except ValidationError as exc:
                self.add_error(None, exc)

        return cleaned

    def montar_dados(self):
        raise NotImplementedError


class QuestaoMultiplaEscolhaForm(QuestaoBaseForm):
    campos_dados = [
        'alternativa_a',
        'alternativa_b',
        'alternativa_c',
        'alternativa_d',
        'gabarito',
        'justificativa',
    ]

    alternativa_a = forms.CharField(
        label='Alternativa A',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 2}),
    )
    alternativa_b = forms.CharField(
        label='Alternativa B',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 2}),
    )
    alternativa_c = forms.CharField(
        label='Alternativa C',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 2}),
    )
    alternativa_d = forms.CharField(
        label='Alternativa D',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 2}),
    )
    gabarito = forms.ChoiceField(
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        label='Alternativa correta',
        widget=forms.Select(attrs={'class': 'sel'}),
    )
    justificativa = forms.CharField(
        required=False,
        label='Justificativa (opcional)',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 3}),
    )

    def montar_dados(self):
        dados = {
            'alternativas': [
                {'letra': 'A', 'texto': self.cleaned_data.get('alternativa_a', '')},
                {'letra': 'B', 'texto': self.cleaned_data.get('alternativa_b', '')},
                {'letra': 'C', 'texto': self.cleaned_data.get('alternativa_c', '')},
                {'letra': 'D', 'texto': self.cleaned_data.get('alternativa_d', '')},
            ],
            'gabarito': self.cleaned_data.get('gabarito'),
        }
        justificativa = self.cleaned_data.get('justificativa')
        if justificativa:
            dados['justificativa'] = justificativa
        return dados


class QuestaoVerdadeiroFalsoForm(QuestaoBaseForm):
    campos_dados = ['resposta', 'justificativa']

    resposta = forms.ChoiceField(
        choices=[('V', 'Verdadeiro'), ('F', 'Falso')],
        label='Resposta correta',
        widget=forms.Select(attrs={'class': 'sel'}),
    )
    justificativa = forms.CharField(
        required=False,
        label='Justificativa (opcional)',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 3}),
    )

    def montar_dados(self):
        dados = {'resposta': self.cleaned_data.get('resposta')}
        justificativa = self.cleaned_data.get('justificativa')
        if justificativa:
            dados['justificativa'] = justificativa
        return dados


class QuestaoDissertativaForm(QuestaoBaseForm):
    campos_dados = ['resposta_esperada']

    resposta_esperada = forms.CharField(
        label='Resposta esperada',
        widget=forms.Textarea(attrs={'class': 'ta', 'rows': 6}),
    )

    def montar_dados(self):
        return {'resposta_esperada': self.cleaned_data.get('resposta_esperada', '')}


class QuestaoLacunasForm(QuestaoBaseForm):
    campos_dados = ['texto_com_lacunas', 'respostas_lacunas']

    texto_com_lacunas = forms.CharField(
        label='Texto com lacunas',
        widget=forms.Textarea(attrs={
            'class': 'ta',
            'rows': 5,
            'placeholder': 'Ex: A fotossíntese ocorre nos ___ e libera ___.',
        }),
    )
    respostas_lacunas = forms.CharField(
        label='Respostas das lacunas',
        widget=forms.Textarea(attrs={
            'class': 'ta',
            'rows': 4,
            'placeholder': 'Uma resposta por linha. Ex:\n1. cloroplastos\n2. oxigênio',
        }),
    )

    def clean_texto_com_lacunas(self):
        texto = self.cleaned_data['texto_com_lacunas']
        if '___' not in texto:
            raise forms.ValidationError('Use ___ para indicar cada lacuna no texto.')
        return texto

    def clean_respostas_lacunas(self):
        respostas = self._respostas_limpas(self.cleaned_data['respostas_lacunas'])
        if not respostas:
            raise forms.ValidationError('Informe pelo menos uma resposta.')
        return '\n'.join(respostas)

    def clean(self):
        cleaned = super().clean()
        texto = cleaned.get('texto_com_lacunas')
        respostas = cleaned.get('respostas_lacunas')
        if texto and respostas:
            total_lacunas = texto.count('___')
            total_respostas = len(self._respostas_limpas(respostas))
            if total_lacunas != total_respostas:
                self.add_error(
                    'respostas_lacunas',
                    f'Informe {total_lacunas} resposta(s), uma para cada lacuna.',
                )
        return cleaned

    def montar_dados(self):
        respostas = [
            {'posicao': index, 'palavra': palavra}
            for index, palavra in enumerate(
                self._respostas_limpas(self.cleaned_data.get('respostas_lacunas', '')),
                start=1,
            )
        ]
        return {
            'texto_com_lacunas': self.cleaned_data.get('texto_com_lacunas', ''),
            'respostas': respostas,
        }

    @staticmethod
    def _respostas_limpas(valor):
        respostas = []
        for linha in (valor or '').splitlines():
            palavra = re.sub(r'^\d+[\).:-]?\s*', '', linha).strip()
            if palavra:
                respostas.append(palavra)
        return respostas


QUESTAO_FORMS_POR_TIPO = {
    Questao.TIPO_MULTIPLA_ESCOLHA: QuestaoMultiplaEscolhaForm,
    Questao.TIPO_VERDADEIRO_FALSO: QuestaoVerdadeiroFalsoForm,
    Questao.TIPO_DISSERTATIVA: QuestaoDissertativaForm,
    Questao.TIPO_LACUNAS: QuestaoLacunasForm,
}


def get_questao_form_class(tipo):
    return QUESTAO_FORMS_POR_TIPO.get(tipo, QuestaoDissertativaForm)


def initial_questao_form(questao):
    initial = {
        'disciplina': questao.disciplina_id,
        'ementa': questao.ementa_id,
        'tipo': questao.tipo,
        'dificuldade': questao.dificuldade,
        'enunciado': questao.enunciado,
    }
    dados = questao.dados or {}

    if questao.tipo == Questao.TIPO_MULTIPLA_ESCOLHA:
        alternativas = {
            item.get('letra'): item.get('texto', '')
            for item in dados.get('alternativas', [])
        }
        initial.update({
            'alternativa_a': alternativas.get('A', ''),
            'alternativa_b': alternativas.get('B', ''),
            'alternativa_c': alternativas.get('C', ''),
            'alternativa_d': alternativas.get('D', ''),
            'gabarito': dados.get('gabarito', 'A'),
            'justificativa': dados.get('justificativa', ''),
        })
    elif questao.tipo == Questao.TIPO_VERDADEIRO_FALSO:
        initial.update({
            'resposta': dados.get('resposta', 'V'),
            'justificativa': dados.get('justificativa', ''),
        })
    elif questao.tipo == Questao.TIPO_DISSERTATIVA:
        initial['resposta_esperada'] = dados.get('resposta_esperada', '')
    elif questao.tipo == Questao.TIPO_LACUNAS:
        respostas = '\n'.join(
            f"{item.get('posicao')}. {item.get('palavra')}"
            for item in dados.get('respostas', [])
        )
        initial.update({
            'texto_com_lacunas': dados.get('texto_com_lacunas', ''),
            'respostas_lacunas': respostas,
        })

    return initial


class ProvaForm(forms.Form):
    titulo = forms.CharField(
        max_length=200,
        label='Título da prova',
        widget=forms.TextInput(attrs={'class': 'inp', 'placeholder': 'Ex: Prova de Matemática - 1º Bimestre'}),
    )
    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.none(),
        label='Disciplina',
        widget=forms.Select(attrs={'class': 'sel'}),
    )
    metodo = forms.ChoiceField(
        choices=[
            ('manual', 'Selecionar manualmente do banco de questões'),
            ('automatico', 'Gerar automaticamente com base em critérios'),
        ],
        label='Método de criação',
        widget=forms.RadioSelect(attrs={'class': 'metodo-radio'}),
        initial='manual',
    )

    # Automatic fields
    ementa = forms.ModelChoiceField(
        queryset=Ementa.objects.none(),
        required=False,
        label='Ementa específica (opcional)',
        widget=forms.Select(attrs={'class': 'sel'}),
    )
    qtd_facil = forms.IntegerField(
        min_value=0,
        initial=0,
        required=False,
        label='Qtd. de questões Fáceis',
        widget=forms.NumberInput(attrs={'class': 'inp', 'min': 0}),
    )
    qtd_medio = forms.IntegerField(
        min_value=0,
        initial=0,
        required=False,
        label='Qtd. de questões Médias',
        widget=forms.NumberInput(attrs={'class': 'inp', 'min': 0}),
    )
    qtd_dificil = forms.IntegerField(
        min_value=0,
        initial=0,
        required=False,
        label='Qtd. de questões Difíceis',
        widget=forms.NumberInput(attrs={'class': 'inp', 'min': 0}),
    )

    # Manual fields
    questoes = forms.ModelMultipleChoiceField(
        queryset=Questao.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Questões',
    )

    def __init__(self, professor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.professor = professor
        self.fields['disciplina'].queryset = Disciplina.objects.filter(professor=professor)
        self.fields['ementa'].queryset = Ementa.objects.filter(disciplina__professor=professor)
        self.fields['questoes'].queryset = Questao.objects.banco().do_professor(professor).select_related('disciplina', 'ementa')

    def clean(self):
        cleaned = super().clean()
        metodo = cleaned.get('metodo')
        disciplina = cleaned.get('disciplina')
        ementa = cleaned.get('ementa')

        if disciplina and ementa and ementa.disciplina_id != disciplina.id:
            self.add_error('ementa', 'A ementa selecionada não pertence a essa disciplina.')

        if metodo == 'manual':
            questoes = cleaned.get('questoes')
            if not questoes:
                self.add_error('questoes', 'Você deve selecionar pelo menos uma questão para a prova.')
            elif disciplina:
                for q in questoes:
                    if q.disciplina_id != disciplina.id:
                        self.add_error('questoes', f'A questão "{q.enunciado[:30]}..." não pertence à disciplina selecionada.')
                        break
        elif metodo == 'automatico':
            q_facil = cleaned.get('qtd_facil') or 0
            q_medio = cleaned.get('qtd_medio') or 0
            q_dificil = cleaned.get('qtd_dificil') or 0
            
            if q_facil + q_medio + q_dificil <= 0:
                self.add_error(None, 'Você deve definir a quantidade maior do que 0 para pelo menos um dos níveis de dificuldade.')

        return cleaned

