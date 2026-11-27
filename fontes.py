"""Apresentação das referências recuperadas pelo RAG, sem depender do Streamlit."""
from collections import defaultdict
from pathlib import PurePosixPath
from urllib.parse import quote
from falabula_core import nome_exibicao

BASE_URL = "https://github.com/Equipe-FalaBula-FMU/Projeto-FalaBula/blob/main/documentos/"

def agrupar_fontes(fontes):
    """Agrupa e ordena páginas; preserva o caminho relativo de cada PDF."""
    grupos = defaultdict(set)
    for fonte in fontes:
        if not isinstance(fonte, str):
            continue
        caminho, separador, pagina = fonte.rpartition(" — página ")
        if not separador or not pagina.isdecimal() or int(pagina) < 1:
            continue
        p = PurePosixPath(caminho)
        if p.is_absolute() or ".." in p.parts or "\\" in caminho or p.suffix.lower() != ".pdf":
            continue
        grupos[p.as_posix()].add(int(pagina))
    resultado = []
    for caminho, paginas in grupos.items():
        p = PurePosixPath(caminho)
        geral = any(x in {"doencas", "protocolos_clinicos", "orientacoes_oficiais"} for x in p.parts[:-1])
        titulo = nome_exibicao(p.name)
        resultado.append({
            "caminho": caminho,
            "titulo": titulo,
            "tipo": "Documento" if geral else "Bula",
            "paginas": sorted(paginas),
            "url": BASE_URL + quote(caminho, safe="/"),
        })
    return resultado
