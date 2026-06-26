import json
import os
import re
import unicodedata
from io import BytesIO
from google import genai
from google.genai import types
from huggingface_hub import InferenceClient

client = genai.Client()
HF_CLIENT = InferenceClient(
    provider='auto',
    token=os.getenv('HF_TOKEN'),
)

def gerar_payload_questoes_gemini(disciplina_id, disciplina_nome, ementa_id, ementa_texto, instrucao, tipo, dificuldade, quantidade):
    
    # 1. Definimos o Schema estruturado para forçar o modelo a obedecer às regras do questoes.py
    esquema_json_esperado = {
        "disciplina_id": str(disciplina_id),
        "ementa_id": str(ementa_id) if ementa_id else None,
        "questoes": [
            {
                "tipo": "Um de: multipla_escolha, verdadeiro_falso, dissertativa, lacunas",
                "enunciado": "Texto da questão",
                "dificuldade": "Um de: facil, medio, dificil",
                "dados": "OBJETO JSON DINÂMICO (VEJA AS REGRAS DO SISTEMA)"
            }
        ]
    }

    # 2. Criamos o prompt dinâmico dando muito contexto sobre a disciplina
    prompt = f"""
    Atue como um professor elaborando avaliações para a disciplina '{disciplina_nome}'.
    Seu objetivo é gerar {quantidade} questões da dificuldade '{dificuldade}' e do tipo '{tipo}'.
    
    Instruções específicas do professor: 
    {instrucao}
    
    Conteúdo base (Ementa):
    {ementa_texto}
    """

    # 3. Passamos as regras de negócio exatas do backend como Instrução de Sistema
    system_instruction = f"""
    Você é um gerador de payload JSON para uma API Django.
    Retorne EXATAMENTE a estrutura: {json.dumps(esquema_json_esperado)}
    
    REGRAS CRÍTICAS PARA O CAMPO "dados" (dependendo do "tipo" gerado):
    
    - Se "multipla_escolha": O objeto deve ter "alternativas" (lista com exatas 4 opções contendo "letra": "A", "B", "C", "D" e "texto": string) e um "gabarito" (string "A", "B", "C" ou "D").
    - Se "verdadeiro_falso": O objeto deve ter apenas "resposta" (string contendo estritamente "V" ou "F").
    - Se "dissertativa": O objeto deve ter apenas "resposta_esperada" (string detalhada).
    - Se "lacunas": O objeto deve ter "texto_com_lacunas" (string que DEVE conter o texto '___' representando os espaços vazios) e "respostas" (lista de objetos com "posicao": numero_inteiro e "palavra": string).
    
    Os ids de disciplina e ementa fornecidos no payload de exemplo devem ser mantidos intactos no retorno.
    Retorne APENAS um JSON válido.
    """

    # 4. Chamada da API forçando o MIME Type
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
            system_instruction=system_instruction
        ),
    )
    
    # O retorno já será um dicionário Python pronto para ser enviado via HTTP ou processado no backend
    return json.loads(response.text)


def _normalizar_prompt_hf(texto):
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ascii', 'ignore').decode('ascii')
    texto = texto.replace('"', '').replace("'", '')
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def gerar_infografico_huggingface(*, disciplina_id, disciplina_nome, ementa_id, ementa_titulo, ementa_texto, descricao='', orientacao_visual=None):
    prompt = (
        f"Crie um infografico educacional com base na ementa abaixo. "
        f"Disciplina: {disciplina_nome}. "
        f"Ementa: {ementa_titulo}. "
        f"Descricao complementar: {descricao or 'Nao informada'}. "
        f"Orientacao visual: {orientacao_visual or 'Visual limpo, claro, pedagogico e facil de ler'}. "
        f"Conteudo base: {ementa_texto}. "
        f"Requisitos: destaque os principais topicos da ementa, use linguagem visual simples e confiavel, evite excesso de texto, priorize hierarquia visual e leitura rapida, o resultado deve ser apropriado para uso em sala de aula."
    )
    prompt = _normalizar_prompt_hf(prompt)

    image = HF_CLIENT.text_to_image(
        prompt=prompt,
        model='black-forest-labs/FLUX.1-schnell',
    )

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    return {
        'texto_resumo': '',
        'imagem_bytes': buffer.read(),
        'filename': f'infografico-{ementa_id}.png',
        'disciplina_id': str(disciplina_id),
        'ementa_id': str(ementa_id),
    }
