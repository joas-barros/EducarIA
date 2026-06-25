from rest_framework import serializers

from .models import Disciplina, Ementa
from .services.questoes import criar_lote_questoes


class LoteQuestaoCreateSerializer(serializers.Serializer):
    disciplina_id = serializers.UUIDField()
    ementa_id = serializers.UUIDField(required=False, allow_null=True)
    questoes = serializers.ListField(child=serializers.JSONField(), allow_empty=False)

    def validate(self, data):
        if 'parametros' in self.initial_data:
            raise serializers.ValidationError({
                'parametros': (
                    'Este campo não é aceito no endpoint de persistência. '
                    'Envie apenas disciplina_id, ementa_id e questoes.'
                ),
            })

        try:
            disciplina = Disciplina.objects.get(id=data['disciplina_id'])
        except Disciplina.DoesNotExist:
            raise serializers.ValidationError({'disciplina_id': 'Disciplina não encontrada.'})

        ementa = None
        ementa_id = data.get('ementa_id')
        if ementa_id:
            try:
                ementa = Ementa.objects.get(id=ementa_id, disciplina=disciplina)
            except Ementa.DoesNotExist:
                raise serializers.ValidationError({'ementa_id': 'Ementa não encontrada.'})

        data['disciplina'] = disciplina
        data['ementa'] = ementa
        return data

    def create(self, validated_data):
        return criar_lote_questoes(
            professor=validated_data['disciplina'].professor,
            disciplina=validated_data['disciplina'],
            ementa=validated_data.get('ementa'),
            questoes=validated_data['questoes'],
        )
