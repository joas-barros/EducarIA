from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from formtools.wizard.views import SessionWizardView

from .forms import (
    CadastroStep1Form, CadastroStep2Form, CadastroStep3Form, LoginForm,
    DisciplinaStep1Form, DisciplinaStep2Form, DisciplinaEditForm,
    EmentaForm, get_questao_form_class, initial_questao_form, ProvaForm,
)
from .models import Disciplina, Ementa, LoteGeracaoQuestao, Questao, Prova
from .services.questoes import (
    aprovar_questao,
    aprovar_todas_questoes,
    editar_e_aprovar_questao,
    formatar_questoes_para_copia,
    linhas_dados_questao,
    rejeitar_questao,
)

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
    disciplinas = request.user.disciplinas.annotate(
        num_ementas=Count('ementas', distinct=True),
        num_questoes=Count(
            'questoes',
            filter=Q(questoes__ativa=True, questoes__status__in=[
                Questao.STATUS_APROVADA,
                Questao.STATUS_EDITADA,
            ]),
            distinct=True,
        ),
    )
    return render(request, 'app/disciplinas.html', {'disciplinas': disciplinas})


@login_required
def disciplina_detalhe(request, pk):
    disciplina = get_object_or_404(Disciplina, id=pk, professor=request.user)
    ementas = disciplina.ementas.all()
    questoes_recentes = (
        disciplina.questoes
        .filter(ativa=True, status__in=[Questao.STATUS_APROVADA, Questao.STATUS_EDITADA])
        .select_related('ementa')
        .order_by('-criado_em')[:5]
    )
    num_questoes = disciplina.questoes.filter(
        ativa=True,
        status__in=[Questao.STATUS_APROVADA, Questao.STATUS_EDITADA],
    ).count()
    return render(request, 'app/disciplina_detalhe.html', {
        'disciplina': disciplina,
        'ementas': ementas,
        'questoes_recentes': questoes_recentes,
        'num_questoes': num_questoes,
    })


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


# ------------------------------------------------------------------ Ementas

@login_required
def ementa_nova(request, disciplina_pk):
    disciplina = get_object_or_404(Disciplina, id=disciplina_pk, professor=request.user)

    if request.method == 'POST':
        form = EmentaForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = form.cleaned_data.get('arquivo')
            texto = (form.cleaned_data.get('texto_colado') or '').strip()

            ementa = Ementa(
                disciplina=disciplina,
                titulo=form.cleaned_data['titulo'],
                descricao=form.cleaned_data.get('descricao', ''),
            )

            if arquivo:
                ementa.tipo_fonte = 'arquivo'
                ementa.arquivo_nome = arquivo.name
                ementa.arquivo_tipo = arquivo.name.rsplit('.', 1)[-1].lower()
                ementa.arquivo_tamanho_bytes = arquivo.size
                ementa.arquivo = arquivo
            else:
                ementa.tipo_fonte = 'texto_colado'
                ementa.texto_colado = texto

            ementa.save()
            return redirect('disciplina_detalhe', pk=disciplina.id)
    else:
        form = EmentaForm()

    return render(request, 'app/ementa_nova.html', {'form': form, 'disciplina': disciplina})


@login_required
def ementa_excluir(request, disciplina_pk, pk):
    disciplina = get_object_or_404(Disciplina, id=disciplina_pk, professor=request.user)
    ementa = get_object_or_404(Ementa, id=pk, disciplina=disciplina)

    if request.method == 'POST':
        if ementa.arquivo:
            try:
                ementa.arquivo.delete(save=False)
            except Exception:
                pass
        ementa.delete()
        return redirect('disciplina_detalhe', pk=disciplina.id)

    return render(request, 'app/ementa_excluir.html', {
        'ementa': ementa,
        'disciplina': disciplina,
    })


# ------------------------------------------------------------------ Questões

def _tipo_questao_requisicao(request, default=Questao.TIPO_DISSERTATIVA):
    tipo = request.POST.get('tipo') if request.method == 'POST' else request.GET.get('tipo')
    tipos_validos = {choice[0] for choice in Questao.TIPO_CHOICES}
    return tipo if tipo in tipos_validos else default


@login_required
def questoes_list(request):
    filtros = {
        'disciplina': request.GET.get('disciplina', ''),
        'ementa': request.GET.get('ementa', ''),
        'tipo': request.GET.get('tipo', ''),
        'dificuldade': request.GET.get('dificuldade', ''),
        'status': request.GET.get('status', ''),
        'q': request.GET.get('q', ''),
    }

    questoes = (
        Questao.objects.banco()
        .do_professor(request.user)
        .select_related('disciplina', 'ementa')
    )

    if filtros['disciplina']:
        questoes = questoes.filter(disciplina_id=filtros['disciplina'])
    if filtros['ementa']:
        questoes = questoes.filter(ementa_id=filtros['ementa'])
    if filtros['tipo']:
        questoes = questoes.filter(tipo=filtros['tipo'])
    if filtros['dificuldade']:
        questoes = questoes.filter(dificuldade=filtros['dificuldade'])
    if filtros['status']:
        questoes = questoes.filter(status=filtros['status'])
    if filtros['q']:
        questoes = questoes.filter(enunciado__icontains=filtros['q'])

    return render(request, 'app/questoes.html', {
        'questoes': questoes,
        'disciplinas': Disciplina.objects.filter(professor=request.user),
        'ementas': Ementa.objects.filter(disciplina__professor=request.user),
        'tipo_choices': Questao.TIPO_CHOICES,
        'dificuldade_choices': Questao.DIFICULDADE_CHOICES,
        'status_choices': [
            (Questao.STATUS_APROVADA, 'Aprovada'),
            (Questao.STATUS_EDITADA, 'Editada'),
        ],
        'filtros': filtros,
    })


@login_required
def questao_nova(request):
    tipo = _tipo_questao_requisicao(request)
    form_class = get_questao_form_class(tipo)
    initial = {
        'tipo': tipo,
        'dificuldade': Questao.DIFICULDADE_MEDIO,
    }
    disciplina_id = request.GET.get('disciplina')
    if disciplina_id:
        initial['disciplina'] = disciplina_id

    if request.method == 'POST':
        form = form_class(request.POST, professor=request.user)
        if form.is_valid():
            dados = form.cleaned_data
            questao = Questao.objects.create(
                disciplina=dados['disciplina'],
                ementa=dados.get('ementa'),
                tipo=dados['tipo'],
                enunciado=dados['enunciado'],
                dificuldade=dados['dificuldade'],
                dados=form.montar_dados(),
                status=Questao.STATUS_APROVADA,
                origem=Questao.ORIGEM_MANUAL,
            )
            return redirect('questao_detalhe', pk=questao.id)
    else:
        form = form_class(professor=request.user, initial=initial)

    return render(request, 'app/questao_form.html', {
        'form': form,
        'titulo': 'Nova questão',
        'subtitulo': 'Cadastro manual direto no Banco de Questões.',
    })


@login_required
def questao_detalhe(request, pk):
    questao = get_object_or_404(
        Questao.objects.ativas().do_professor(request.user).select_related('disciplina', 'ementa'),
        id=pk,
    )
    return render(request, 'app/questao_detalhe.html', {
        'questao': questao,
        'dados_linhas': linhas_dados_questao(questao),
    })


@login_required
def questao_editar(request, pk):
    questao = get_object_or_404(
        Questao.objects.ativas().do_professor(request.user).select_related('disciplina', 'ementa', 'lote'),
        id=pk,
    )
    status_anterior = questao.status
    tipo = _tipo_questao_requisicao(request, default=questao.tipo)
    form_class = get_questao_form_class(tipo)

    if request.method == 'POST':
        form = form_class(request.POST, professor=request.user)
        if form.is_valid():
            dados = form.cleaned_data
            editar_e_aprovar_questao(
                questao,
                enunciado=dados['enunciado'],
                tipo=dados['tipo'],
                dificuldade=dados['dificuldade'],
                dados=form.montar_dados(),
            )
            questao.disciplina = dados['disciplina']
            questao.ementa = dados.get('ementa')
            questao.save(update_fields=['disciplina', 'ementa', 'atualizado_em'])
            if status_anterior == Questao.STATUS_GERADA and questao.lote_id:
                return redirect('questoes_revisao_lote', pk=questao.lote_id)
            return redirect('questao_detalhe', pk=questao.id)
    else:
        if tipo == questao.tipo:
            initial = initial_questao_form(questao)
        else:
            initial = {
                'disciplina': questao.disciplina_id,
                'ementa': questao.ementa_id,
                'tipo': tipo,
                'dificuldade': questao.dificuldade,
                'enunciado': questao.enunciado,
            }
        form = form_class(professor=request.user, initial=initial)

    return render(request, 'app/questao_form.html', {
        'form': form,
        'titulo': 'Editar questão',
        'subtitulo': 'Ao salvar, a questão fica com status editada.',
        'questao': questao,
    })


@login_required
def questao_excluir(request, pk):
    questao = get_object_or_404(
        Questao.objects.banco().do_professor(request.user).select_related('disciplina'),
        id=pk,
    )

    if request.method == 'POST':
        questao.delete()
        return redirect('questoes')

    return render(request, 'app/questao_excluir.html', {'questao': questao})


@login_required
@require_POST
def questoes_copiar(request):
    ids = request.POST.getlist('questoes')
    questoes = list(
        Questao.objects.banco()
        .do_professor(request.user)
        .filter(id__in=ids)
        .select_related('disciplina', 'ementa')
    )
    texto = formatar_questoes_para_copia(questoes)
    if request.POST.get('download') == '1':
        return HttpResponse(texto, content_type='text/plain; charset=utf-8')
    return render(request, 'app/questoes_copiar.html', {
        'questoes': questoes,
        'texto': texto,
    })


@login_required
def questoes_revisao_lote(request, pk):
    lote = get_object_or_404(
        LoteGeracaoQuestao.objects.select_related('disciplina', 'ementa'),
        id=pk,
        professor=request.user,
    )
    questoes = list(lote.questoes.filter(
        ativa=True,
        status=Questao.STATUS_GERADA,
    ).order_by('criado_em'))
    for questao in questoes:
        questao.dados_linhas = linhas_dados_questao(questao)
    revisadas = lote.questoes.filter(
        status__in=[Questao.STATUS_APROVADA, Questao.STATUS_EDITADA],
    ).count()

    return render(request, 'app/questoes_revisao.html', {
        'lote': lote,
        'questoes': questoes,
        'revisadas': revisadas,
    })


@login_required
@require_POST
def questoes_aprovar_todas(request, lote_pk):
    lote = get_object_or_404(LoteGeracaoQuestao, id=lote_pk, professor=request.user)
    aprovar_todas_questoes(lote)
    return redirect('questoes_revisao_lote', pk=lote.id)


@login_required
@require_POST
def questao_aprovar(request, pk):
    questao = get_object_or_404(
        Questao.objects.geradas().do_professor(request.user),
        id=pk,
    )
    lote_id = questao.lote_id
    aprovar_questao(questao)
    if lote_id:
        return redirect('questoes_revisao_lote', pk=lote_id)
    return redirect('questoes')


@login_required
@require_POST
def questao_rejeitar(request, pk):
    questao = get_object_or_404(
        Questao.objects.geradas().do_professor(request.user),
        id=pk,
    )
    lote_id = questao.lote_id
    rejeitar_questao(questao)
    if lote_id:
        return redirect('questoes_revisao_lote', pk=lote_id)
    return redirect('questoes')


@login_required
def provas_list(request):
    provas = Prova.objects.filter(professor=request.user).select_related('disciplina')
    return render(request, 'app/provas.html', {
        'provas': provas,
        'active_page': 'provas',
    })


@login_required
def prova_nova(request):
    if request.method == 'POST':
        form = ProvaForm(request.user, request.POST)
        if form.is_valid():
            titulo = form.cleaned_data['titulo']
            disciplina = form.cleaned_data['disciplina']
            metodo = form.cleaned_data['metodo']

            if metodo == 'manual':
                questoes = form.cleaned_data['questoes']
                prova = Prova.objects.create(
                    titulo=titulo,
                    disciplina=disciplina,
                    professor=request.user,
                )
                prova.questoes.set(questoes)
                return redirect('prova_detalhe', pk=prova.id)

            elif metodo == 'automatico':
                dificuldade = form.cleaned_data['dificuldade']
                ementa = form.cleaned_data['ementa']
                quantidade = form.cleaned_data['quantidade']

                qs = Questao.objects.banco().filter(disciplina=disciplina)
                if dificuldade:
                    qs = qs.filter(dificuldade=dificuldade)
                if ementa:
                    qs = qs.filter(ementa=ementa)

                questoes = list(qs.order_by('?')[:quantidade])

                if not questoes:
                    form.add_error(None, 'Nenhuma questão foi encontrada no banco correspondente aos critérios selecionados. Adicione mais questões ou mude os filtros.')
                else:
                    prova = Prova.objects.create(
                        titulo=titulo,
                        disciplina=disciplina,
                        professor=request.user,
                    )
                    prova.questoes.set(questoes)
                    return redirect('prova_detalhe', pk=prova.id)
    else:
        form = ProvaForm(request.user)

    questoes = Questao.objects.banco().do_professor(request.user).select_related('ementa').values(
        'id', 'enunciado', 'tipo', 'dificuldade', 'disciplina_id', 'ementa__titulo'
    )
    questoes_list = list(questoes)
    for q in questoes_list:
        q['id'] = str(q['id'])
        q['disciplina_id'] = str(q['disciplina_id'])
        q['tipo_display'] = dict(Questao.TIPO_CHOICES).get(q['tipo'], q['tipo'])
        q['dificuldade_display'] = dict(Questao.DIFICULDADE_CHOICES).get(q['dificuldade'], q['dificuldade'])
        q['ementa_titulo'] = q['ementa__titulo'] or ''

    ementas = Ementa.objects.filter(disciplina__professor=request.user).values('id', 'titulo', 'disciplina_id')
    ementas_list = list(ementas)
    for e in ementas_list:
        e['id'] = str(e['id'])
        e['disciplina_id'] = str(e['disciplina_id'])

    import json
    return render(request, 'app/prova_form.html', {
        'form': form,
        'questoes_json': json.dumps(questoes_list),
        'ementas_json': json.dumps(ementas_list),
        'active_page': 'provas',
    })


@login_required
def prova_detalhe(request, pk):
    prova = get_object_or_404(
        Prova.objects.filter(professor=request.user).select_related('disciplina'),
        id=pk
    )
    questoes = prova.questoes.all().select_related('ementa')
    
    if 'pdf' in request.GET:
        from io import BytesIO
        from django.template.loader import get_template
        from xhtml2pdf import pisa
        
        com_gabarito = request.GET.get('gabarito') == '1'
        
        context = {
            'prova': prova,
            'questoes': questoes,
            'com_gabarito': com_gabarito,
        }
        
        template = get_template('app/prova_pdf.html')
        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
        
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            suffix = "gabarito" if com_gabarito else "prova"
            filename = f"{suffix}_{prova.titulo.replace(' ', '_')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            return HttpResponse("Erro ao gerar PDF", status=500)

    if 'download' in request.GET or 'copiar' in request.GET:
        com_gabarito = request.GET.get('gabarito') == '1'
        texto = formatar_questoes_para_copia(list(questoes), com_gabarito=com_gabarito)
        tipo_documento = "GABARITO" if com_gabarito else "PROVA"
        cabecalho = f"{tipo_documento}: {prova.titulo.upper()}\nDISCIPLINA: {prova.disciplina.nome.upper()}\nPROFESSOR(A): {prova.professor.get_full_name().upper()}\nDATA: {prova.criado_em.strftime('%d/%m/%Y')}\n"
        cabecalho += "="*60 + "\n\n"
        texto_completo = cabecalho + texto
        
        if 'download' in request.GET:
            response = HttpResponse(texto_completo, content_type='text/plain; charset=utf-8')
            suffix = "gabarito" if com_gabarito else "prova"
            filename = f"{suffix}_{prova.titulo.replace(' ', '_')}.txt"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        return render(request, 'app/prova_copiar.html', {
            'prova': prova,
            'questoes': questoes,
            'texto': texto_completo,
            'com_gabarito': com_gabarito,
        })
        
    return render(request, 'app/prova_detalhe.html', {
        'prova': prova,
        'questoes': questoes,
        'active_page': 'provas',
    })


@login_required
def prova_excluir(request, pk):
    prova = get_object_or_404(
        Prova.objects.filter(professor=request.user),
        id=pk
    )
    if request.method == 'POST':
        prova.delete()
        return redirect('provas')
    return render(request, 'app/prova_excluir.html', {
        'prova': prova,
        'active_page': 'provas',
    })

