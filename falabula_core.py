"""Núcleo do FalaBula: catálogo verificável, leitura de PDFs e recuperação segura.

Não utiliza serviços externos para reconhecer medicamentos ou listar a base.
A API Groq é acionada somente depois de selecionar a bula correta.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import math
import re
import unicodedata

CATALOGO = {
    "bula_Mounjaro.pdf": ("Mounjaro", ("mounjaro", "monjaro", "tirzepatida")),
    "bula_LANTUS_insulina_glargina.pdf": ("Lantus", ("lantus", "insulina glargina", "glargina")),
    "bula_InsulinaHumanaRegular.pdf": ("Wosulin R", ("wosulin", "insulina humana regular", "insulina regular")),
    "bula_InsulinaHumana_NovolinN.pdf": ("Novolin N", ("novolin", "insulina nph", "insulina humana nph")),
    "bula_empagliflozina.pdf": ("Empagliflozina", ("empagliflozina",)),
    "bula_dapagliflozina.pdf": ("Dapagliflozina", ("dapagliflozina",)),
    "bula_Januvia.pdf": ("Januvia", ("januvia", "sitagliptina")),
    "bula_glimepirida.pdf": ("Glimepirida", ("glimepirida",)),
    "bula_gliclazida.pdf": ("Gliclazida", ("gliclazida",)),
    "bula_glibenclamida.pdf": ("Glibenclamida", ("glibenclamida",)),
    "bula_glifagexr.pdf": ("Glifage XR", ("glifage xr",)),
    "bula_glifage.pdf": ("Glifage", ("glifage",)),
}

# Algumas palavras são comuns a muitos PDFs; não podem identificar um produto.
PALAVRAS_COMUNS = {
    "qual", "quais", "quero", "saber", "sobre", "para", "serve", "servem",
    "bula", "bulas", "medicamento", "medicamentos", "remedio", "remedios",
    "informacao", "informacoes", "com", "sem", "dos", "das", "uma", "por",
    "seus", "seja", "pode", "devo", "usar", "uso", "ter", "tem", "texto",
    "segundo", "nome", "nomes", "quero", "preciso", "liste", "lista",
    "cadastrados", "disponiveis", "projeto", "chatbot", "falabula",
    "efeitos", "colaterais", "indicacao", "indicacoes", "contraindicacoes",
}

def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()

def listar_arquivos(pasta: Path) -> list[Path]:
    return sorted(
        [p for p in pasta.rglob("*.pdf") if p.is_file()],
        key=lambda p: p.name.casefold(),
    ) if pasta.is_dir() else []

def assinatura(arquivos: list[Path]) -> tuple:
    """Identifica alterações sem ler novamente cada PDF em cada mensagem."""
    return tuple(
        (str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in arquivos
    )

def chave_documento(p: Path) -> str:
    # Caminho relativo à base evita colisões entre PDFs homônimos.
    partes = p.parts
    if "documentos" in partes:
        return "/".join(partes[partes.index("documentos") + 1:])
    return p.name

def documento_geral(p: Path) -> bool:
    return any(x in {"doencas", "protocolos_clinicos", "orientacoes_oficiais"} for x in p.parts[:-1])

def nome_exibicao(nome_arquivo: str) -> str:
    if nome_arquivo in CATALOGO:
        return CATALOGO[nome_arquivo][0]
    return Path(nome_arquivo).stem.removeprefix("bula_").replace("_", " ")

def pergunta_catalogo(pergunta: str) -> bool:
    p = normalizar(pergunta)
    if p in ("o que voce conhece", "o que tem na base", "que medicamentos tem"):
        return True
    objeto = re.search(r"\b(medicamentos?|remedios?|bulas?|farmacos?|documentos?)\b", p)
    if not objeto:
        return False
    # Perguntas clínicas não são pedidos de catálogo.
    if re.search(r"\b(efeitos?|reacoes|contraindicacoes|indicacoes|posologia|dose|trata|tratam|diabetes|pressao|doenca|doencas)\b", p):
        return False
    return bool(re.search(r"\b(cadastrad[oa]s?|disponiveis|registrad[oa]s?|catalogo|liste|listar|quantos|quantas|lista)\b", p)
                or re.search(r"\b(na base|no sistema|no falabula)\b", p))

def resposta_catalogo(arquivos: list[Path]) -> str:
    arquivos = [p for p in arquivos if not documento_geral(p)]
    linhas = [f"{i}. {nome_exibicao(p.name)}" for i, p in enumerate(arquivos, 1)]
    return (
        f"Há **{len(arquivos)} bulas em PDF** na base do FalaBula:\n\n"
        + "\n".join(linhas)
        + "\n\nEsta lista corresponde aos arquivos cadastrados. "
        "Não confirma disponibilidade no SUS, Farmácia Popular ou estoque."
    )

def identificar_documentos(pergunta: str, arquivos: list[Path]) -> list[Path]:
    """Exige correspondência explícita e inequívoca com o nome/princípio ativo."""
    frase = " " + normalizar(pergunta) + " "
    # Normaliza também o erro comum Monjaro -> Mounjaro.
    frase = frase.replace(" monjaro ", " mounjaro ")
    correspondencias = {}
    for p in arquivos:
        if documento_geral(p):
            continue
        if p.name in CATALOGO:
            apelidos = CATALOGO[p.name][1]
        else:
            apelidos = (normalizar(nome_exibicao(p.name)),)
        melhor = 0
        for alias in apelidos:
            token = " " + normalizar(alias) + " "
            if len(token.strip()) >= 3 and token in frase:
                melhor = max(melhor, len(token.strip()))
        if melhor:
            correspondencias[p] = melhor

    # Um nome de marca específico prevalece sobre a forma genérica.
    # "Glifage XR" não deve retornar "Glifage" comum.
    if correspondencias:
        maior = max(correspondencias.values())
        # Exclui apenas nomes contidos em outro alias mais específico.
        selecionados = list(correspondencias)
        for curto in list(selecionados):
            aliases = CATALOGO.get(curto.name, ("", (nome_exibicao(curto.name),)))[1]
            if any(
                normalizar(a) != normalizar(b) and (" " + normalizar(a) + " ") in (" " + normalizar(b) + " ")
                and (" " + normalizar(b) + " ") in frase
                for outro in correspondencias if outro != curto
                for a in aliases
                for b in CATALOGO.get(outro.name, ("", (nome_exibicao(outro.name),)))[1]
                if (" " + normalizar(a) + " ") in frase
            ):
                selecionados.remove(curto)
        return selecionados

    return []

def carregar_paginas(arquivos: list[Path]) -> dict[str, list[tuple[int, str]]]:
    """Indexa somente texto legível. PDFs inválidos são reportados ao usuário."""
    from pypdf import PdfReader

    base = {}
    falhas = []
    for arquivo in arquivos:
        try:
            paginas = []
            for i, pagina in enumerate(PdfReader(str(arquivo)).pages, 1):
                texto = (pagina.extract_text() or "").strip()
                if texto:
                    paginas.append((i, texto))
            if not paginas:
                falhas.append(f"{arquivo.name}: não possui texto selecionável")
            else:
                base[chave_documento(arquivo)] = paginas
        except Exception as erro:
            falhas.append(f"{arquivo.name}: PDF inválido ({type(erro).__name__})")
    if falhas:
        raise RuntimeError("Revise os documentos: " + "; ".join(falhas))
    return base

def foco(pergunta: str) -> str:
    p = normalizar(pergunta)
    if any(x in p for x in ("para que serve", "indicado", "indicacao", "indicações", "trata", "tratamento")):
        return "indicacao"
    if any(x in p for x in ("contraindic", "nao devo", "nao pode usar")):
        return "contraindicacao"
    if any(x in p for x in ("reacao adversa", "reacoes adversas", "efeito colateral", "efeitos colaterais", "males pode")):
        return "reacoes"
    if any(x in p for x in ("como usar", "posologia", "dose", "dosagem")):
        return "posologia"
    return "geral"

ANCORAS = {
    "indicacao": ("para que este medicamento e indicado", "indicacoes", "para que serve"),
    "contraindicacao": ("quando nao devo usar este medicamento", "contraindicacoes"),
    "reacoes": ("quais os males que este medicamento pode me causar", "reacoes adversas"),
    "posologia": ("como devo usar este medicamento", "posologia"),
}

def recuperar_paginas(pergunta: str, documentos: list[Path], base: dict,
                     limite: int = 4) -> list[tuple[str, int, str]]:
    """Nunca mistura medicamentos: busca apenas nos PDFs selecionados."""
    objetivo = foco(pergunta)
    termos = set(normalizar(pergunta).split()) - PALAVRAS_COMUNS
    candidatos = []
    for arquivo in documentos:
        for numero, texto in base.get(chave_documento(arquivo), base.get(arquivo.name, [])):
            conteudo = normalizar(texto)
            ocorrencias = sum(min(conteudo.count(t), 8) for t in termos if len(t) > 3)
            ancoras = ANCORAS.get(objetivo, ())
            bonus = 12 if any(a in conteudo for a in ancoras) else 0
            bonus += 2 if numero <= 3 else 0
            candidatos.append((bonus + ocorrencias, chave_documento(arquivo), numero, texto))

    candidatos.sort(key=lambda x: (-x[0], x[1], x[2]))
    saida = []
    for nota, nome, pagina, texto in candidatos[:limite]:
        # Textos longos são limitados para controlar custos e contexto.
        bruto = normalizar(texto)
        posicoes = [bruto.find(a) for a in ANCORAS.get(objetivo, ()) if a in bruto]
        # A pagina inteira, limitada, preserva a estrutura das instruções.
        saida.append((nome, pagina, texto[:4200]))
    return saida

def limpar_referencias_tecnicas(resposta: str) -> str:
    """Remove apenas marcadores técnicos de página/documento gerados pelo modelo.

    Mantém siglas médicas, números, unidades e parágrafos do texto.
    As fontes são retornadas separadamente pelo mecanismo de recuperação.
    """
    padrao = r"[【\[]\s*(?:(?:DOCUMENTO|FONTE)\s*:\s*[^【】\[\]\n]*?\|\s*)?P[ÁA]GINAS?\s*:\s*\d+(?:\s*(?:[,;–-]|e)\s*\d+)*\s*[】\]]"
    resposta = re.sub(r"[ \t]*" + padrao, "", resposta, flags=re.IGNORECASE)
    return resposta.strip()


def responder_pergunta(pergunta: str, arquivos: list[Path], base: dict,
                      api_key: str) -> tuple[str, list[str]]:
    if not arquivos:
        return "A pasta documentos não possui arquivos PDF.", []
    if pergunta_catalogo(pergunta) and not identificar_documentos(pergunta, arquivos):
        return resposta_catalogo(arquivos), []

    encontrados = identificar_documentos(pergunta, arquivos)
    consulta_geral = not encontrados
    if consulta_geral:
        p = normalizar(pergunta)
        # Não buscar doses ou recomendações de medicamentos sem identificar o produto.
        if foco(pergunta) in {"posologia", "contraindicacao", "reacoes"} or any(
            t in p for t in ("qual remedio", "qual medicamento", "quais remedios", "quais medicamentos", "devo tomar", "posso tomar", "me receite", "farmacia popular", "estoque", "preco", "disponivel no sus")
        ):
            return "Informe o nome do medicamento para consultar sua bula. Não posso prescrever tratamentos.", []
        # Prioriza fontes gerais; admite bulas como fontes limitadas de informação.
        termos = {t for t in p.split() if len(t) > 3 and t not in PALAVRAS_COMUNS
                  and t not in {"tipos", "tipo", "quais", "quaisquer", "diferenca", "explique", "principais", "existem", "existe", "conhecidos", "classificacao"}}
        if not termos:
            return "Especifique a doença ou assunto que deseja consultar.", []
        candidatos = []
        chaves_gerais = {chave_documento(a) for a in arquivos if documento_geral(a)}
        for arquivo in arquivos:
            for numero, texto in base.get(chave_documento(arquivo), base.get(arquivo.name, [])):
                palavras = set(normalizar(texto).split())
                comuns = termos & palavras
                if comuns:
                    nota = len(comuns) * 10 + (30 if documento_geral(arquivo) else 0)
                    if "tipos" in p.split() or "tipo" in p.split():
                        nota += 5 * int("tipo" in palavras or "tipos" in palavras)
                        nota += 8 * int("classificacao" in palavras or "classificacoes" in palavras)
                    candidatos.append((nota, chave_documento(arquivo), numero, texto))
        candidatos.sort(key=lambda x: (-x[0], x[1], x[2]))
        # Fontes gerais relevantes prevalecem sobre bulas em perguntas conceituais.
        gerais = [item for item in candidatos if item[1] in chaves_gerais]
        if gerais:
            candidatos = gerais
        trechos = []
        contagem = Counter()
        for _, nome, pagina, texto in candidatos:
            if contagem[nome] >= (6 if nome in chaves_gerais else 2):
                continue
            trechos.append((nome, pagina, texto[:4200]))
            contagem[nome] += 1
            if len(trechos) >= 6:
                break
        if not trechos:
            return "Não encontrei informações documentais sobre esse assunto na base cadastrada.", []
    if len(encontrados) > 1:
        nomes = ", ".join(nome_exibicao(p.name) for p in encontrados)
        return f"Encontrei mais de uma bula correspondente: **{nomes}**. Especifique a apresentação.", []

    if not consulta_geral:
        trechos = recuperar_paginas(pergunta, encontrados, base)
    if not trechos:
        return "Não foi possível extrair informações da bula selecionada.", []

    fontes = [f"{nome} — página {pagina}" for nome, pagina, _ in trechos]
    contexto = "\n\n".join(
        f"DOCUMENTO: {nome} | PÁGINA: {pagina}\n{texto}"
        for nome, pagina, texto in trechos
    )

    if not api_key:
        return (
            "Os documentos foram localizados, mas a chave da API Groq não está configurada. "
            "Verifique os Secrets do Streamlit.", fontes
        )

    # A seleção da bula ocorre antes de qualquer chamada ao modelo de linguagem.
    from groq import Groq
    mensagens = [
        {"role": "system", "content": (
            "Você é um assistente acadêmico de consulta a bulas. " +
            ("Responda em português claro somente com os documentos apresentados. "
             "Em perguntas gerais, explique apenas o que os trechos sustentam, distinguindo bulas de diretrizes; "
             "não trate indicações de medicamentos como classificação completa de doenças. Use as fontes gerais recuperadas como referência principal e não extrapole os trechos. "
             "Se a base não permitir uma resposta completa, declare a limitação. "
             "Não recomende medicamentos nem misture orientações de produtos distintos. "
             if consulta_geral else "Responda em português claro somente com o texto da bula apresentada. Identifique o medicamento pelo nome da bula. ") + 
            "Nunca invente dose, indicação, apresentação, tempo de ação, "
            "interação, contraindicação, fonte ou disponibilidade gratuita. "
            "Se o trecho não contém a resposta, declare que não foi possível "
            "confirmá-la nos trechos recuperados. "
            "Não faça diagnóstico, prescrição nem recomendação individual. "
            "Resuma somente informações pertinentes à pergunta. "
            "Não atribua informações de um medicamento a outro. Escreva a resposta em linguagem natural, sem marcadores técnicos de documento ou página, sem referências entre colchetes e sem listas de fontes no corpo do texto. A interface apresenta separadamente os documentos e páginas recuperados. Preserve siglas médicas relevantes e explique seus significados quando necessário."
        )},
        {"role": "user", "content": f"PERGUNTA: {pergunta}\n\nDOCUMENTOS RECUPERADOS:\n{contexto}"}
    ]
    resultado = Groq(api_key=api_key, timeout=30.0, max_retries=0).chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=mensagens,
        temperature=0,
        max_completion_tokens=900,
    )
    resposta = limpar_referencias_tecnicas(resultado.choices[0].message.content or "")
    if not resposta:
        raise RuntimeError("O serviço de geração retornou uma resposta vazia.")
    return resposta, fontes
