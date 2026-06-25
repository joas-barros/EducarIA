from django.contrib import admin
from .models import Disciplina, Ementa, LoteGeracaoQuestao, Professor, Questao

admin.site.register(Professor)
admin.site.register(Disciplina)
admin.site.register(Ementa)
admin.site.register(LoteGeracaoQuestao)
admin.site.register(Questao)
