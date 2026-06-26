
# EducarIA 🎓🤖

**EducarIA** é uma plataforma inovadora de gestão pedagógica desenhada para otimizar a rotina de professores. O sistema permite o cadastro de turmas, o gerenciamento de ementas escolares e a geração automatizada de materiais didáticos através de Inteligência Artificial Generativa.

Com o EducarIA, educadores podem poupar horas de trabalho manual criando questões, avaliações completas, infográficos e flashcards com o poder do **Google Gemini 2.5 Flash** e **Hugging Face (Flux.1-schnell)**.

---

## ✨ Principais Funcionalidades

* **Gestão de Disciplinas e Ementas:** Cadastro de turmas com detalhes (nível, turno, série) e upload de ementas via arquivo (PDF, DOCX, TXT) ou texto colado.
* **Geração Inteligente de Questões (Gemini API):** Criação de lotes de questões (Múltipla Escolha, Verdadeiro/Falso, Dissertativas e Lacunas) perfeitamente alinhadas ao conteúdo da ementa e instruções do professor.
* **Banco de Questões:** Acervo pessoal de questões aprovadas, com sistema de busca, filtragem (por dificuldade, tipo, ementa) e opção de cópia formatada (para alunos ou gabarito para professores).
* **Criação de Provas:** Geração de avaliações manuais (escolhendo do banco) ou automáticas (sorteio balanceado por dificuldade). Permite a exportação direta da prova e do gabarito em **PDF**.
* **Flashcards Interativos:** Geração de baralhos de estudo (frente e verso) a partir das questões, com uma interface gamificada em 3D para revisão.
* **Infográficos Educacionais (Hugging Face):** Transformação do texto da ementa em material visual atrativo para a sala de aula usando o modelo de IA de imagens FLUX.1.

---

## 🛠️ Tecnologias Utilizadas

**Backend:**

* [Python 3](https://www.python.org/)
* [Django](https://www.djangoproject.com/) (Framework MTV)
* [Django REST Framework](https://www.django-rest-framework.org/) (Endpoints da IA)
* [PostgreSQL](https://www.postgresql.org/) (Banco de Dados)

**Inteligência Artificial:**

* [Google GenAI SDK](https://pypi.org/project/google-genai/) (Integração com Gemini 2.5 Flash)
* [Hugging Face Hub](https://huggingface.co/) (Integração para geração de imagens)

**Frontend & Outros:**

* HTML5, CSS3 nativo (variáveis CSS, Grid, Flexbox)
* JavaScript (Manipulação de DOM e animações 3D para os Flashcards)
* `xhtml2pdf` (Geração de documentos PDF)
* `django-formtools` (Formulários em múltiplas etapas / Wizards)
* `python-dotenv` (Gerenciamento seguro de variáveis de ambiente)

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos

* Python 3.10+
* PostgreSQL instalado e rodando
* Chave de API do **Google AI Studio** (`GEMINI_API_KEY`)
* Token de acesso do **Hugging Face** (`HF_TOKEN`)

### 1. Clonar o Repositório

```bash
git clone [https://github.com/seu-usuario/educaria.git](https://github.com/seu-usuario/educaria.git)
cd educaria
```
