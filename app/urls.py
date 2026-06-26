from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/cadastro/', views.CadastroWizardView.as_view(views.CADASTRO_FORMS), name='cadastro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('disciplinas/', views.disciplinas_list, name='disciplinas'),
    path('disciplinas/nova/', views.DisciplinaCreateView.as_view(views.DISCIPLINA_FORMS), name='disciplina_nova'),
    path('disciplinas/<uuid:pk>/', views.disciplina_detalhe, name='disciplina_detalhe'),
    path('disciplinas/<uuid:pk>/editar/', views.disciplina_editar, name='disciplina_editar'),
    path('disciplinas/<uuid:pk>/excluir/', views.disciplina_excluir, name='disciplina_excluir'),

    path('disciplinas/<uuid:disciplina_pk>/ementas/nova/', views.ementa_nova, name='ementa_nova'),
    path('disciplinas/<uuid:disciplina_pk>/ementas/<uuid:pk>/excluir/', views.ementa_excluir, name='ementa_excluir'),

    path('questoes/', views.questoes_list, name='questoes'),
    path('questoes/gerar/', views.questoes_gerar, name='questoes_gerar'),
    path('questoes/gerar/processando/', views.questoes_gerar_processando, name='questoes_gerar_processando'),
    path('questoes/revisoes/pendentes/', views.questoes_revisoes_pendentes, name='questoes_revisoes_pendentes'),
    path('questoes/nova/', views.questao_nova, name='questao_nova'),
    path('questoes/copiar/', views.questoes_copiar, name='questoes_copiar'),
    path('questoes/lotes/<uuid:pk>/revisao/', views.questoes_revisao_lote, name='questoes_revisao_lote'),
    path('questoes/lotes/<uuid:lote_pk>/aprovar-todas/', views.questoes_aprovar_todas, name='questoes_aprovar_todas'),
    path('questoes/<uuid:pk>/', views.questao_detalhe, name='questao_detalhe'),
    path('questoes/<uuid:pk>/editar/', views.questao_editar, name='questao_editar'),
    path('questoes/<uuid:pk>/excluir/', views.questao_excluir, name='questao_excluir'),
    path('questoes/<uuid:pk>/aprovar/', views.questao_aprovar, name='questao_aprovar'),
    path('questoes/<uuid:pk>/rejeitar/', views.questao_rejeitar, name='questao_rejeitar'),

    # Provas
    path('provas/', views.provas_list, name='provas'),
    path('provas/nova/', views.prova_nova, name='prova_nova'),
    path('provas/<uuid:pk>/', views.prova_detalhe, name='prova_detalhe'),
    path('provas/<uuid:pk>/excluir/', views.prova_excluir, name='prova_excluir'),
]
