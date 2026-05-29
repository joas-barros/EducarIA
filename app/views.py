from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from formtools.wizard.views import SessionWizardView

from .forms import (
    CadastroStep1Form, CadastroStep2Form, CadastroStep3Form, LoginForm,
    DisciplinaStep1Form, DisciplinaStep2Form, DisciplinaEditForm,
)
from .models import Disciplina

Professor = get_user_model()

# ------------------------------------------------------------------ Cadastro

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

        # Auto-criação da Disciplina inicial (spec §1.1)
        Disciplina.objects.create(
            professor=professor,
            nome=data['disciplina_principal'],
            nivel=data['nivel_ensino'],
        )

        login(self.request, professor)
        return redirect('dashboard')


# ------------------------------------------------------------------ Auth

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


# ------------------------------------------------------------------ Dashboard

@login_required
def dashboard_view(request):
    total_disciplinas = request.user.disciplinas.count()
    return render(request, 'app/dashboard.html', {'total_disciplinas': total_disciplinas})


# ------------------------------------------------------------------ Disciplinas

DISCIPLINA_FORMS = [
    ('dados', DisciplinaStep1Form),
    ('config_ia', DisciplinaStep2Form),
]


class DisciplinaCreateView(LoginRequiredMixin, SessionWizardView):
    template_name = 'app/disciplina_nova.html'

    def done(self, form_list, **kwargs):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)

        config_ia = None
        if data.get('dificuldade_padrao') or data.get('tipos_preferidos') or data.get('observacoes_ia'):
            config_ia = {
                'dificuldade_padrao': data.get('dificuldade_padrao') or 'mix',
                'tipos_preferidos': list(data.get('tipos_preferidos') or []),
                'observacoes_ia': data.get('observacoes_ia') or '',
            }

        Disciplina.objects.create(
            professor=self.request.user,
            nome=data['nome'],
            nivel=data['nivel'],
            serie_ano=data.get('serie_ano', ''),
            turno=data.get('turno', ''),
            num_alunos_estimado=data.get('num_alunos_estimado'),
            periodo_inicio=data.get('periodo_inicio'),
            periodo_fim=data.get('periodo_fim'),
            config_ia=config_ia,
        )
        return redirect('disciplinas')


@login_required
def disciplinas_list(request):
    disciplinas = request.user.disciplinas.all()
    return render(request, 'app/disciplinas.html', {'disciplinas': disciplinas})


@login_required
def disciplina_detalhe(request, pk):
    disciplina = get_object_or_404(Disciplina, id=pk, professor=request.user)
    return render(request, 'app/disciplina_detalhe.html', {'disciplina': disciplina})


@login_required
def disciplina_editar(request, pk):
    disciplina = get_object_or_404(Disciplina, id=pk, professor=request.user)
    config = disciplina.config_ia or {}

    if request.method == 'POST':
        form = DisciplinaEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            disciplina.nome = d['nome']
            disciplina.nivel = d['nivel']
            disciplina.serie_ano = d.get('serie_ano', '')
            disciplina.turno = d.get('turno', '')
            disciplina.num_alunos_estimado = d.get('num_alunos_estimado')
            disciplina.periodo_inicio = d.get('periodo_inicio')
            disciplina.periodo_fim = d.get('periodo_fim')

            if d.get('dificuldade_padrao') or d.get('tipos_preferidos') or d.get('observacoes_ia'):
                disciplina.config_ia = {
                    'dificuldade_padrao': d.get('dificuldade_padrao') or 'mix',
                    'tipos_preferidos': list(d.get('tipos_preferidos') or []),
                    'observacoes_ia': d.get('observacoes_ia') or '',
                }
            else:
                disciplina.config_ia = None

            disciplina.save()
            return redirect('disciplina_detalhe', pk=disciplina.id)
    else:
        initial = {
            'nome': disciplina.nome,
            'nivel': disciplina.nivel,
            'serie_ano': disciplina.serie_ano,
            'turno': disciplina.turno,
            'num_alunos_estimado': disciplina.num_alunos_estimado,
            'periodo_inicio': disciplina.periodo_inicio,
            'periodo_fim': disciplina.periodo_fim,
            'dificuldade_padrao': config.get('dificuldade_padrao', 'mix'),
            'tipos_preferidos': config.get('tipos_preferidos', []),
            'observacoes_ia': config.get('observacoes_ia', ''),
        }
        form = DisciplinaEditForm(initial=initial)

    return render(request, 'app/disciplina_editar.html', {'form': form, 'disciplina': disciplina})


@login_required
def disciplina_excluir(request, pk):
    disciplina = get_object_or_404(Disciplina, id=pk, professor=request.user)
    if request.method == 'POST':
        disciplina.soft_delete()
        return redirect('disciplinas')
    return render(request, 'app/disciplina_excluir.html', {'disciplina': disciplina})
