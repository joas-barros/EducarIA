from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/cadastro/', views.CadastroWizardView.as_view(views.CADASTRO_FORMS), name='cadastro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
