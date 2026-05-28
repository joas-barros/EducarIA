from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from formtools.wizard.views import SessionWizardView

from .forms import CadastroStep1Form, CadastroStep2Form, CadastroStep3Form, LoginForm

Professor = get_user_model()

CADASTRO_FORMS = [
    ('dados_pessoais', CadastroStep1Form),
    ('perfil_docente', CadastroStep2Form),
    ('acesso', CadastroStep3Form),
]


class CadastroWizardView(SessionWizardView):
    template_name = 'app/cadastro.html'

    def done(self, form_list, **kwargs):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)

        professor = Professor.objects.create_user(
            email=data['email'],
            username=data['email'],
            first_name=data['nome'],
            last_name=data['sobrenome'],
            password=data['senha'],
            trabalha_com_idiomas=data.get('trabalha_com_idiomas', False),
        )
        # disciplina_principal e nivel_ensino coletados no Step 2 apenas para UX — descartados aqui
        # TODO (feature Disciplinas): usar esses valores para criar a Disciplina inicial do professor

        login(self.request, professor)
        return redirect('dashboard')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm()
    error = None

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            professor = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['senha'],
            )
            if professor is not None:
                login(request, professor)
                return redirect('dashboard')
            error = 'E-mail ou senha incorretos.'

    return render(request, 'app/login.html', {'form': form, 'error': error})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    return render(request, 'app/dashboard.html')
