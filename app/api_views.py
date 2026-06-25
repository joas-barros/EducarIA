from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoteQuestaoCreateSerializer


class IALoteQuestoesCreateAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoteQuestaoCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        lote, criadas, erros = serializer.save()
        questoes_recebidas = len(request.data.get('questoes') or [])

        if lote is None:
            raise ValidationError({
                'erro': 'nenhuma_questao_valida',
                'questoes_recebidas': questoes_recebidas,
                'questoes_criadas': 0,
                'erros': erros,
            })

        return Response({
            'lote_id': str(lote.id),
            'questoes_recebidas': questoes_recebidas,
            'questoes_criadas': len(criadas),
            'questoes_ignoradas': len(erros),
            'status': 'gerada',
            'review_url': reverse('questoes_revisao_lote', kwargs={'pk': lote.id}),
            'erros': erros,
        }, status=status.HTTP_201_CREATED)
