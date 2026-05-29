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
]
