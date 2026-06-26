from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Disciplina, Ementa, LoteFlashcard, Questao
from .services.questoes import criar_lote_flashcard


Professor = get_user_model()


class FlashcardLoteViewTests(TestCase):
    def setUp(self):
        self.professor = Professor.objects.create_user(
            username='professor@example.com',
            email='professor@example.com',
            password='senha-forte-123',
        )
        self.disciplina = Disciplina.objects.create(
            professor=self.professor,
            nome='Biologia',
            nivel='Ensino Médio',
        )
        self.ementa = Ementa.objects.create(
            disciplina=self.disciplina,
            titulo='Citologia',
            tipo_fonte='texto_colado',
            texto_colado='Organelas celulares',
        )
        self.questao = Questao.objects.create(
            disciplina=self.disciplina,
            ementa=self.ementa,
            tipo=Questao.TIPO_DISSERTATIVA,
            enunciado='Explique a função dos ribossomos.',
            dificuldade=Questao.DIFICULDADE_MEDIO,
            status=Questao.STATUS_APROVADA,
            origem=Questao.ORIGEM_MANUAL,
            dados={'resposta_esperada': 'Produzir proteínas a partir do RNA mensageiro.'},
        )
        self.outra_questao = Questao.objects.create(
            disciplina=self.disciplina,
            ementa=self.ementa,
            tipo=Questao.TIPO_VERDADEIRO_FALSO,
            enunciado='Ribossomos participam da síntese proteica.',
            dificuldade=Questao.DIFICULDADE_FACIL,
            status=Questao.STATUS_APROVADA,
            origem=Questao.ORIGEM_MANUAL,
            dados={'resposta': 'V'},
        )

    def test_renderiza_conteudo_das_questoes_no_json_do_lote(self):
        lote = LoteFlashcard.objects.create(
            professor=self.professor,
            disciplina=self.disciplina,
            ementa=self.ementa,
            quantidade_recebida=1,
        )
        lote.questoes.add(self.questao)

        self.client.force_login(self.professor)
        response = self.client.get(reverse('flashcards_lote', args=[lote.id]))

        self.assertContains(response, 'Explique a função dos ribossomos.')
        self.assertContains(response, 'Produzir proteínas a partir do RNA mensageiro.')
        flashcards = response.context['flashcards_json']
        self.assertIsInstance(flashcards, list)
        self.assertEqual(flashcards[0]['frente'], self.questao.enunciado)
        self.assertEqual(flashcards[0]['verso'], self.questao.dados['resposta_esperada'])

    def test_criar_flashcard_reaproveita_lote_existente_da_ementa(self):
        primeiro_lote = criar_lote_flashcard(
            professor=self.professor,
            disciplina=self.disciplina,
            ementa=self.ementa,
            questoes=[self.questao],
        )
        segundo_lote = criar_lote_flashcard(
            professor=self.professor,
            disciplina=self.disciplina,
            ementa=self.ementa,
            questoes=[self.questao, self.outra_questao],
        )

        self.assertEqual(primeiro_lote.id, segundo_lote.id)
        self.assertEqual(LoteFlashcard.objects.filter(ementa=self.ementa).count(), 1)
        self.assertEqual(segundo_lote.questoes.count(), 2)
        self.assertEqual(segundo_lote.quantidade_recebida, 2)

    def test_crud_edita_e_exclui_flashcard(self):
        lote = criar_lote_flashcard(
            professor=self.professor,
            disciplina=self.disciplina,
            ementa=self.ementa,
            questoes=[self.questao],
        )

        self.client.force_login(self.professor)
        response = self.client.post(reverse('flashcards_editar', args=[lote.id]), {
            'ementa': str(self.ementa.id),
            'questoes': [str(self.questao.id), str(self.outra_questao.id)],
        })
        self.assertRedirects(response, reverse('flashcards_lote', args=[lote.id]))
        lote.refresh_from_db()
        self.assertEqual(lote.questoes.count(), 2)

        response = self.client.post(reverse('flashcards_excluir', args=[lote.id]))
        self.assertRedirects(response, reverse('flashcards'))
        self.assertFalse(LoteFlashcard.objects.filter(id=lote.id).exists())
