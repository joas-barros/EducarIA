from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from app.models import LoteGeracaoQuestao, Questao


def _erro(mensagem, codigo='dados_invalidos', campo=None):
    raise ValidationError(mensagem, code=codigo, params={'campo': campo})


def _primeiro_erro(exc):
    if hasattr(exc, 'error_list') and exc.error_list:
        return exc.error_list[0]
    return exc


def formatar_erro_validacao(index, exc):
    erro = _primeiro_erro(exc)
    params = getattr(erro, 'params', None) or {}
    mensagem = getattr(erro, 'message', str(erro))
    if params:
        try:
            mensagem = mensagem % params
        except (KeyError, TypeError, ValueError):
            pass
    return {
        'index': index,
        'codigo': getattr(erro, 'code', None) or 'dados_invalidos',
        'campo': params.get('campo'),
        'mensagem': mensagem,
    }


def validar_dados_questao(tipo, dados):
    if not isinstance(dados, dict):
        _erro('O campo dados deve ser um objeto JSON.', campo='dados')

    if tipo == Questao.TIPO_MULTIPLA_ESCOLHA:
        _validar_multipla_escolha(dados)
    elif tipo == Questao.TIPO_VERDADEIRO_FALSO:
        _validar_verdadeiro_falso(dados)
    elif tipo == Questao.TIPO_DISSERTATIVA:
        _validar_dissertativa(dados)
    elif tipo == Questao.TIPO_LACUNAS:
        _validar_lacunas(dados)
    else:
        _erro('Tipo de questão inválido.', codigo='tipo_invalido', campo='tipo')


def validar_item_questao(item):
    if not isinstance(item, dict):
        _erro('Cada questão deve ser um objeto JSON.', codigo='item_invalido')

    tipo = item.get('tipo')
    enunciado = item.get('enunciado')
    dificuldade = item.get('dificuldade')
    dados = item.get('dados')

    tipos_validos = {choice[0] for choice in Questao.TIPO_CHOICES}
    dificuldades_validas = {choice[0] for choice in Questao.DIFICULDADE_CHOICES}

    if tipo not in tipos_validos:
        _erro('Tipo de questão inválido.', codigo='tipo_invalido', campo='tipo')
    if dificuldade not in dificuldades_validas:
        _erro('Dificuldade inválida.', codigo='dificuldade_invalida', campo='dificuldade')
    if not isinstance(enunciado, str) or not enunciado.strip():
        _erro('Enunciado é obrigatório.', codigo='campo_obrigatorio', campo='enunciado')

    validar_dados_questao(tipo, dados)

    return {
        'tipo': tipo,
        'enunciado': enunciado.strip(),
        'dificuldade': dificuldade,
        'dados': dados,
    }


def _validar_multipla_escolha(dados):
    alternativas = dados.get('alternativas')
    if not isinstance(alternativas, list) or len(alternativas) != 4:
        _erro(
            'Múltipla escolha deve ter exatamente quatro alternativas.',
            campo='dados.alternativas',
        )

    letras_esperadas = ['A', 'B', 'C', 'D']
    letras = []
    for index, alternativa in enumerate(alternativas):
        if not isinstance(alternativa, dict):
            _erro('Cada alternativa deve ser um objeto JSON.', campo=f'dados.alternativas.{index}')
        letra = alternativa.get('letra')
        texto = alternativa.get('texto')
        if letra not in letras_esperadas:
            _erro('Alternativa deve usar letra A, B, C ou D.', campo=f'dados.alternativas.{index}.letra')
        if not isinstance(texto, str) or not texto.strip():
            _erro('Texto da alternativa é obrigatório.', campo=f'dados.alternativas.{index}.texto')
        letras.append(letra)

    if sorted(letras) != letras_esperadas:
        _erro('Alternativas devem conter exatamente as letras A, B, C e D.', campo='dados.alternativas')

    if dados.get('gabarito') not in letras_esperadas:
        _erro('Gabarito deve ser A, B, C ou D.', campo='dados.gabarito')


def _validar_verdadeiro_falso(dados):
    if dados.get('resposta') not in ['V', 'F']:
        _erro('Resposta deve ser V ou F.', campo='dados.resposta')


def _validar_dissertativa(dados):
    resposta = dados.get('resposta_esperada')
    if not isinstance(resposta, str) or not resposta.strip():
        _erro('Resposta esperada é obrigatória.', codigo='campo_obrigatorio', campo='dados.resposta_esperada')


def _validar_lacunas(dados):
    texto = dados.get('texto_com_lacunas')
    if not isinstance(texto, str) or not texto.strip():
        _erro('Texto com lacunas é obrigatório.', codigo='campo_obrigatorio', campo='dados.texto_com_lacunas')
    if '___' not in texto:
        _erro('Texto com lacunas deve conter ___.', campo='dados.texto_com_lacunas')

    respostas = dados.get('respostas')
    if not isinstance(respostas, list) or not respostas:
        _erro('Respostas das lacunas são obrigatórias.', codigo='campo_obrigatorio', campo='dados.respostas')

    for index, resposta in enumerate(respostas):
        if not isinstance(resposta, dict):
            _erro('Cada resposta deve ser um objeto JSON.', campo=f'dados.respostas.{index}')
        posicao = resposta.get('posicao')
        palavra = resposta.get('palavra')
        if not isinstance(posicao, int) or posicao < 1:
            _erro('Posição da lacuna deve ser um inteiro positivo.', campo=f'dados.respostas.{index}.posicao')
        if not isinstance(palavra, str) or not palavra.strip():
            _erro('Palavra da lacuna é obrigatória.', campo=f'dados.respostas.{index}.palavra')


def criar_lote_questoes(*, professor, disciplina, ementa=None, questoes=None):
    if disciplina.professor_id != professor.id:
        raise PermissionDenied('Disciplina não pertence ao professor autenticado.')

    if ementa and ementa.disciplina_id != disciplina.id:
        raise ValidationError('Ementa não pertence à disciplina informada.')

    questoes = questoes or []
    questoes_validas = []
    erros = []

    for index, item in enumerate(questoes):
        try:
            questoes_validas.append(validar_item_questao(item))
        except ValidationError as exc:
            erros.append(formatar_erro_validacao(index, exc))

    if not questoes_validas:
        return None, [], erros

    lote = LoteGeracaoQuestao.objects.create(
        professor=professor,
        disciplina=disciplina,
        ementa=ementa,
        quantidade_recebida=len(questoes),
    )

    objetos = [
        Questao(
            disciplina=disciplina,
            ementa=ementa,
            lote=lote,
            tipo=item['tipo'],
            enunciado=item['enunciado'],
            dificuldade=item['dificuldade'],
            dados=item['dados'],
            status=Questao.STATUS_GERADA,
            origem=Questao.ORIGEM_IA,
        )
        for item in questoes_validas
    ]
    criadas = Questao.objects.bulk_create(objetos)
    return lote, criadas, erros


def aprovar_questao(questao):
    questao.status = Questao.STATUS_APROVADA
    questao.save(update_fields=['status', 'atualizado_em'])
    return questao


def editar_e_aprovar_questao(questao, *, enunciado, tipo, dificuldade, dados):
    validar_dados_questao(tipo, dados)
    questao.enunciado = enunciado
    questao.tipo = tipo
    questao.dificuldade = dificuldade
    questao.dados = dados
    questao.status = Questao.STATUS_EDITADA
    questao.save()
    return questao


def rejeitar_questao(questao):
    if questao.status != Questao.STATUS_GERADA:
        raise ValidationError('Apenas questões geradas podem ser rejeitadas.')
    questao.delete()


def aprovar_todas_questoes(lote):
    return lote.questoes.filter(
        ativa=True,
        status=Questao.STATUS_GERADA,
    ).update(
        status=Questao.STATUS_APROVADA,
        atualizado_em=timezone.now(),
    )


def linhas_dados_questao(questao):
    dados = questao.dados or {}
    linhas = []

    if questao.tipo == Questao.TIPO_MULTIPLA_ESCOLHA:
        for alternativa in dados.get('alternativas', []):
            linhas.append({
                'rotulo': f"Alternativa {alternativa.get('letra', '')}",
                'valor': alternativa.get('texto', ''),
            })
        linhas.append({'rotulo': 'Gabarito', 'valor': dados.get('gabarito', '')})
    elif questao.tipo == Questao.TIPO_VERDADEIRO_FALSO:
        resposta = dados.get('resposta', '')
        resposta_legivel = {'V': 'Verdadeiro', 'F': 'Falso'}.get(resposta, resposta)
        linhas.append({'rotulo': 'Resposta correta', 'valor': resposta_legivel})
    elif questao.tipo == Questao.TIPO_DISSERTATIVA:
        linhas.append({'rotulo': 'Resposta esperada', 'valor': dados.get('resposta_esperada', '')})
    elif questao.tipo == Questao.TIPO_LACUNAS:
        linhas.append({'rotulo': 'Texto com lacunas', 'valor': dados.get('texto_com_lacunas', '')})
        respostas = ', '.join(
            f"{item.get('posicao')}: {item.get('palavra')}"
            for item in dados.get('respostas', [])
        )
        linhas.append({'rotulo': 'Respostas', 'valor': respostas})

    justificativa = dados.get('justificativa')
    if justificativa:
        linhas.append({'rotulo': 'Justificativa', 'valor': justificativa})

    return linhas


def formatar_questoes_para_copia(questoes, com_gabarito=True):
    partes = []
    for numero, questao in enumerate(questoes, start=1):
        partes.append(_formatar_questao_para_copia(numero, questao, com_gabarito))
    return '\n\n'.join(partes)


def _formatar_questao_para_copia(numero, questao, com_gabarito=True):
    linhas = [
        f'{numero}. {questao.enunciado}',
    ]
    if com_gabarito:
        linhas.append(f'Tipo: {questao.get_tipo_display()} | Dificuldade: {questao.get_dificuldade_display()}')
    
    dados = questao.dados or {}

    if questao.tipo == Questao.TIPO_MULTIPLA_ESCOLHA:
        for alternativa in dados.get('alternativas', []):
            linhas.append(f"{alternativa.get('letra')}) {alternativa.get('texto')}")
        if com_gabarito:
            linhas.append(f"Gabarito: {dados.get('gabarito', '')}")
    elif questao.tipo == Questao.TIPO_VERDADEIRO_FALSO:
        if com_gabarito:
            linhas.append(f"Resposta: {dados.get('resposta', '')}")
    elif questao.tipo == Questao.TIPO_DISSERTATIVA:
        if com_gabarito:
            linhas.append(f"Resposta esperada: {dados.get('resposta_esperada', '')}")
        else:
            # Add some blank lines for students to write answers
            linhas.append('\n' + '_' * 60 + '\n' + '_' * 60 + '\n')
    elif questao.tipo == Questao.TIPO_LACUNAS:
        linhas.append(f"Texto: {dados.get('texto_com_lacunas', '')}")
        if com_gabarito:
            respostas = ', '.join(
                f"{item.get('posicao')}: {item.get('palavra')}"
                for item in dados.get('respostas', [])
            )
            linhas.append(f"Respostas: {respostas}")

    if com_gabarito:
        justificativa = dados.get('justificativa')
        if justificativa:
            linhas.append(f'Justificativa: {justificativa}')

    return '\n'.join(linhas)
