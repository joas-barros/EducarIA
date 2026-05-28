from django import forms
from django.contrib.auth import get_user_model

Professor = get_user_model()

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
