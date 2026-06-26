from dotenv import load_dotenv

# 1. Carrega as variáveis de ambiente PRIMEIRO
load_dotenv()

# 2. SÓ DEPOIS importa o serviço que vai usar a chave
from app.services.ia import *
import json

if __name__ == "__main__":
    load_dotenv()
    print("Iniciando geração com Gemini 2.5 Flash...\n")
    
    # Dados fictícios para simular a requisição do frontend
    teste_disciplina_id = "c8f83088-b8ec-4785-a8ee-8273b04b05d8"
    teste_ementa_id = "a1b2c3d4-e5f6-7890-1234-56789abcdef0"
    
    try:
        resultado = gerar_payload_questoes_gemini(
            disciplina_id=teste_disciplina_id,
            disciplina_nome="História Geral",
            ementa_id=teste_ementa_id,
            ementa_texto="O período da Idade Moderna, com foco especial nas Grandes Navegações, a queda de Constantinopla e o início do Renascimento.",
            instrucao="Faça questões curtas e diretas, sem pegadinhas.",
            tipo="multipla_escolha", # Testando o formato mais complexo
            dificuldade="facil",
            quantidade=2
        )
        
        print("✅ SUCESSO! JSON Retornado:\n")
        # Imprime o JSON de forma legível e identada
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print("❌ ERRO DURANTE A GERAÇÃO:")
        print(str(e))

