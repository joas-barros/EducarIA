from django.contrib import admin
from .models import Disciplina, Ementa, Infografico, LoteGeracaoQuestao, Professor, Questao, Prova

admin.site.register(Professor)
admin.site.register(Disciplina)
admin.site.register(Ementa)
admin.site.register(Infografico)
admin.site.register(LoteGeracaoQuestao)
admin.site.register(Questao)
admin.site.register(Prova)
