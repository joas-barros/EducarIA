from django.urls import path

from . import api_views

urlpatterns = [
    path(
        'ia/questoes/lotes/',
        api_views.IALoteQuestoesCreateAPIView.as_view(),
        name='api_ia_questoes_lotes',
    ),
]
