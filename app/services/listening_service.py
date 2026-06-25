"""
app/services/listening_service.py
----------------------------------
Camada de serviço do módulo de Listening.

Responsabilidades:
  1. Construir o prompt e chamar Gemini Flash para gerar o roteiro
  2. Chamar Google Cloud TTS para sintetizar o áudio
  3. Salvar o MP3 no campo FileField do model

Dependências (adicionar ao requirements.txt):
  google-generativeai
  google-cloud-texttospeech
"""

import io
import logging
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Geração de roteiro com Gemini Flash
# ---------------------------------------------------------------------------

def gerar_roteiro(
    idioma: str,
    nivel: str,
    contexto: str,
    tema_livre: str = '',
) -> str:
    """
    Chama Gemini Flash e retorna o roteiro gerado como string.

    Parâmetros
    ----------
    idioma      : 'en' ou 'es'
    nivel       : 'A2', 'B1' ou 'B2'
    contexto    : texto extraído da ementa (ou tema livre se ementa ausente)
    tema_livre  : instrução adicional do professor

    Retorna
    -------
    str com o roteiro pronto para ser lido em voz alta
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except ImportError:
        logger.error('google-generativeai não instalado. Rode: pip install google-generativeai')
        raise
    except AttributeError:
        logger.error('GEMINI_API_KEY não configurado em settings.py')
        raise

    idioma_nome = {'en': 'Inglês', 'es': 'Espanhol'}.get(idioma, idioma)
    nivel_desc = {
        'A2': 'iniciante (A2) — vocabulário simples, frases curtas',
        'B1': 'intermediário (B1) — vocabulário moderado, estruturas variadas',
        'B2': 'avançado (B2) — vocabulário rico, estruturas complexas',
    }.get(nivel, nivel)

    prompt = f"""
Você é um especialista em criação de materiais didáticos para ensino de idiomas.

Crie um exercício de listening em {idioma_nome} para alunos de nível {nivel_desc}.

{'Contexto da ementa do professor:' if contexto else ''}
{contexto}

{'Instrução adicional do professor: ' + tema_livre if tema_livre else ''}

Requisitos do roteiro:
- Escreva APENAS o texto que será narrado em voz alta — sem títulos, sem "Roteiro:", sem explicações
- Use o idioma {idioma_nome} em todo o texto (sem misturar português)
- Duração estimada: 45 a 90 segundos quando lido em velocidade normal
- Deve ser uma conversa ou monólogo natural e realista
- O nível de dificuldade deve ser {nivel_desc}
- Incorpore estruturas gramaticais e vocabulário relevantes para o nível
- Termine com uma pergunta ou situação que estimule reflexão
""".strip()

    response = model.generate_content(prompt)
    return response.text.strip()


# ---------------------------------------------------------------------------
# 2. Síntese de áudio com Google Cloud TTS
# ---------------------------------------------------------------------------

def sintetizar_audio(roteiro: str, voz: str, idioma: str) -> bytes:
    """
    Chama Google Cloud TTS e retorna os bytes MP3.

    Parâmetros
    ----------
    roteiro : texto a ser sintetizado
    voz     : nome da voz Cloud TTS (ex: 'en-US-Neural2-F')
    idioma  : 'en' ou 'es' — usado para derivar o language_code

    Retorna
    -------
    bytes do arquivo MP3
    """
    try:
        from google.cloud import texttospeech
    except ImportError:
        logger.error('google-cloud-texttospeech não instalado. '
                     'Rode: pip install google-cloud-texttospeech')
        raise

    # Deriva o language_code a partir do nome da voz (primeiros 5 chars: 'en-US')
    language_code = voz[:5]

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=roteiro)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voz,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,    # professor pode pedir lento/rápido via pitch futuro
        pitch=0.0,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice_params,
        audio_config=audio_config,
    )
    return response.audio_content


# ---------------------------------------------------------------------------
# 3. Orquestrador principal — chamado pelas views
# ---------------------------------------------------------------------------

def criar_exercicio_listening(exercicio) -> None:
    """
    Recebe uma instância de ExercicioListening já salva no banco
    (sem roteiro nem áudio) e preenche os campos via IA.

    Fluxo:
      1. Extrai contexto da ementa (se houver)
      2. Gera roteiro com Gemini Flash
      3. Sintetiza áudio com Cloud TTS
      4. Calcula duração aproximada
      5. Salva tudo no model

    Uso nas views:
        exercicio = ExercicioListening(disciplina=..., ...)
        exercicio.save()
        criar_exercicio_listening(exercicio)
    """
    # 1. Contexto da ementa
    contexto = ''
    if exercicio.ementa:
        ementa = exercicio.ementa
        if ementa.tipo_fonte == 'texto_colado':
            contexto = ementa.texto_colado[:3000]  # limita tokens
        elif ementa.arquivo:
            contexto = _extrair_texto_ementa(ementa)

    # 2. Roteiro via Gemini Flash
    roteiro = gerar_roteiro(
        idioma=exercicio.idioma,
        nivel=exercicio.nivel,
        contexto=contexto,
        tema_livre=exercicio.tema_livre,
    )
    exercicio.roteiro = roteiro

    # 3. Áudio via Cloud TTS
    audio_bytes = sintetizar_audio(
        roteiro=roteiro,
        voz=exercicio.voz,
        idioma=exercicio.idioma,
    )

    # 4. Duração estimada (~150 palavras/minuto)
    palavras = len(roteiro.split())
    exercicio.audio_duracao_segundos = max(10, int((palavras / 150) * 60))

    # 5. Salva o arquivo e persiste
    exercicio.audio.save(
        f'{exercicio.id}.mp3',
        ContentFile(audio_bytes),
        save=False,
    )
    exercicio.save(update_fields=['roteiro', 'audio', 'audio_duracao_segundos'])


def regenerar_audio(exercicio) -> None:
    """
    Regera apenas o áudio a partir do roteiro atual (editado pelo professor).
    Não chama Gemini — só Cloud TTS.
    """
    audio_bytes = sintetizar_audio(
        roteiro=exercicio.roteiro,
        voz=exercicio.voz,
        idioma=exercicio.idioma,
    )

    palavras = len(exercicio.roteiro.split())
    exercicio.audio_duracao_segundos = max(10, int((palavras / 150) * 60))

    # Apaga o arquivo antigo antes de salvar o novo
    if exercicio.audio:
        try:
            exercicio.audio.delete(save=False)
        except Exception:
            pass

    exercicio.audio.save(
        f'{exercicio.id}.mp3',
        ContentFile(audio_bytes),
        save=False,
    )
    exercicio.save(update_fields=['audio', 'audio_duracao_segundos', 'atualizado_em'])


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _extrair_texto_ementa(ementa) -> str:
    """
    Extrai texto de arquivo PDF, DOCX ou TXT da ementa.
    Retorna string (pode ser vazia em caso de falha).
    """
    import os
    if not ementa.arquivo:
        return ''

    path = ementa.arquivo.path
    ext = (ementa.arquivo_tipo or '').lower()

    try:
        if ext == 'txt':
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(3000)

        elif ext == 'pdf':
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    texto = '\n'.join(
                        page.extract_text() or '' for page in pdf.pages[:5]
                    )
                return texto[:3000]
            except ImportError:
                logger.warning('pdfplumber não instalado — PDF não extraído')
                return ''

        elif ext == 'docx':
            try:
                from docx import Document
                doc = Document(path)
                texto = '\n'.join(p.text for p in doc.paragraphs)
                return texto[:3000]
            except ImportError:
                logger.warning('python-docx não instalado — DOCX não extraído')
                return ''

    except Exception as e:
        logger.error(f'Erro ao extrair texto da ementa {ementa.id}: {e}')

    return ''
