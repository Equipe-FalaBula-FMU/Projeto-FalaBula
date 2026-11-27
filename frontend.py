"""FalaBula — interface de consulta a bulas PDF, sem alteração do app.py original.

Execute na raiz do repositório: python -m streamlit run frontend.py
Novos PDFs em documentos/ são reconhecidos após atualização/recarga da aplicação.
"""
from pathlib import Path
import hashlib
import os

import streamlit as st
from dotenv import load_dotenv
from fontes import agrupar_fontes

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "documentos"
load_dotenv(BASE_DIR / ".env")
st.set_page_config(
    page_title="FalaBula | Assistente de bulas",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS_FILE = BASE_DIR / "style.css"
if CSS_FILE.exists():
    st.markdown(
        f'<style>{CSS_FILE.read_text(encoding="utf-8")}</style>',
        unsafe_allow_html=True,
    )

if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False
if "mensagens_falabula" not in st.session_state:
    st.session_state.mensagens_falabula = []
if "nome_visitante" not in st.session_state:
    st.session_state.nome_visitante = "Visitante"


from falabula_core import (
    listar_arquivos, assinatura, carregar_paginas, responder_pergunta,
    pergunta_catalogo, resposta_catalogo, identificar_documentos, documento_geral, chave_documento
)


def listar_bulas():
    return listar_arquivos(DOCS_DIR)


def assinatura_documentos(arquivos):
    return assinatura(arquivos)


@st.cache_resource(show_spinner=False, max_entries=2)
def indexar_documentos(identificacao):
    """Carrega os PDFs uma vez; mudanças de arquivo invalidam o cache."""
    return carregar_paginas(listar_bulas())


def chave_groq():
    """Compatível com .env local e Streamlit Cloud Secrets."""
    chave = os.getenv("GROQ_API_KEY", "")
    if chave:
        return chave
    try:
        return st.secrets.get("GROQ_API_KEY", "")
    except (FileNotFoundError, KeyError):
        return ""


def mostrar_fontes(fontes):
    grupos = agrupar_fontes(fontes)
    if not grupos:
        return
    with st.expander("Fontes consultadas", expanded=False):
        for grupo in grupos:
            st.text(f"{grupo['tipo']} — {grupo['titulo']}")
            paginas = ", ".join(str(p) for p in grupo["paginas"])
            st.caption(f"Páginas recuperadas: {paginas}")
            rotulo = "Ler bula completa (PDF)" if grupo["tipo"] == "Bula" else "Ler documento completo (PDF)"
            st.link_button(rotulo, grupo["url"])
        st.caption("Estas páginas foram recuperadas para a consulta. Confira o PDF completo para confirmar as informações. O link abre a versão cadastrada no GitHub, não necessariamente a revisão mais recente do fabricante.")


def responder(pergunta, identificacao):
    arquivos = listar_bulas()
    if pergunta_catalogo(pergunta) and not identificar_documentos(pergunta, arquivos):
        return resposta_catalogo(arquivos), []
    indice = indexar_documentos(identificacao)
    return responder_pergunta(pergunta, arquivos, indice, chave_groq())


st.markdown(
    '<div class="top-brand"><div class="brand-mark">F</div><div>'
    '<div class="brand-name">FalaBula<span>.</span></div>'
    '<div class="brand-subtitle">Informações sobre medicamentos e saúde, baseadas em documentos</div>'
    '</div><span class="top-pill">PROJETO ACADÊMICO</span></div>',
    unsafe_allow_html=True,
)

if not st.session_state.acesso_liberado:
    left, center, right = st.columns([1, 1.18, 1])
    with center:
        st.markdown(
            '<div class="login-intro"><div class="eyebrow">BEM-VINDO AO FALABULA</div>'
            '<h1>Informação clara.<br><em>Consulta responsável.</em></h1>'
            '<p>Pesquise informações sobre medicamentos nos documentos '
            'de bula cadastrados pela equipe.</p></div>',
            unsafe_allow_html=True,
        )
        with st.form("acesso_demo", border=False):
            usuario = st.text_input(
                "Seu nome", placeholder="Como podemos chamar você?"
            )
            st.text_input(
                "Senha demonstrativa", type="password",
                placeholder="Qualquer senha (opcional)"
            )
            entrar = st.form_submit_button(
                "Acessar o assistente →", use_container_width=True, type="primary"
            )
            if entrar:
                st.session_state.nome_visitante = usuario.strip() or "Visitante"
                st.session_state.acesso_liberado = True
                st.rerun()
        st.caption(
            "Acesso demonstrativo: não há autenticação de usuários."
        )
else:
    st.markdown(
        '<div class="hero"><div class="eyebrow">SEU ASSISTENTE DE BULAS</div>'
        '<h1>Como podemos <em>ajudar você?</em></h1>'
        '<p>Consulte indicações, precauções, contraindicações e reações adversas '
        'de medicamentos e temas de saúde presentes na base documental.</p></div>',
        unsafe_allow_html=True,
    )
    arquivos = listar_bulas()
    assinatura = assinatura_documentos(arquivos)
    with st.sidebar:
        st.markdown("### FalaBula")
        st.write(f"Olá, **{st.session_state.nome_visitante}**.")
        if st.button("Nova conversa", use_container_width=True):
            st.session_state.mensagens_falabula = []
            st.rerun()
        if st.button("Sair da demonstração", use_container_width=True):
            st.session_state.acesso_liberado = False
            st.session_state.mensagens_falabula = []
            st.rerun()
        st.divider()
        st.caption(f"Bulas cadastradas: {sum(not documento_geral(p) for p in arquivos)}")
        st.caption(f"Documentos gerais: {sum(documento_geral(p) for p in arquivos)}")
        st.caption("Versão 2.5 — respostas e fontes — 27/11/2026")
        with st.expander("Documentos disponíveis"):
            for arquivo in arquivos:
                st.caption(chave_documento(arquivo))
        st.caption(
            "Projeto acadêmico. Informações não substituem orientação "
            "médica ou farmacêutica."
        )

    if not arquivos:
        st.warning(
            "Nenhum PDF encontrado na pasta documentos. "
            "Inclua arquivos PDF de bula e atualize a aplicação."
        )

    if not st.session_state.mensagens_falabula:
        st.markdown(
            '<div class="suggest-title">Você pode começar por uma destas perguntas:</div>',
            unsafe_allow_html=True,
        )
        temas = [
            "Quais medicamentos estão cadastrados no FalaBula?",
            "Para que serve o Mounjaro, segundo a bula?",
            "Quais contraindicações constam na bula do Glifage?",
            "Quais reações adversas constam na bula do Januvia?",
            "Quais os tipos de diabetes?",

        ]
        grade = st.columns(2)
        selecionada = None
        for i, tema in enumerate(temas):
            with grade[i % 2]:
                if st.button(tema + "  ↗", key=f"sug_{i}", use_container_width=True):
                    selecionada = tema
    else:
        selecionada = None

    for mensagem in st.session_state.mensagens_falabula:
        with st.chat_message(
            mensagem["role"],
            avatar="👤" if mensagem["role"] == "user" else "💬",
        ):
            st.markdown(mensagem["content"])
            mostrar_fontes(mensagem.get("fontes", []))

    pergunta_digitada = st.chat_input(
        "Pergunte sobre medicamentos ou assuntos presentes nos documentos..."
    )
    pergunta = pergunta_digitada or selecionada
    if pergunta:
        st.session_state.mensagens_falabula.append(
            {"role": "user", "content": pergunta}
        )
        with st.chat_message("user", avatar="👤"):
            st.markdown(pergunta)
        with st.chat_message("assistant", avatar="💬"):
            try:
                with st.spinner("Consultando documentos cadastrados..."):
                    resposta, fontes = responder(pergunta, assinatura)
            except Exception as erro:
                st.error(f"Não foi possível consultar os documentos: {erro}")
            else:
                st.markdown(resposta)
                mostrar_fontes(fontes)
                st.session_state.mensagens_falabula.append(
                    {"role": "assistant", "content": resposta, "fontes": fontes}
                )

    st.markdown(
        '<div class="medical-note"><strong>Atenção:</strong> '
        'conteúdo informativo e acadêmico. Não inicie, suspenda ou altere '
        'medicamentos sem orientação médica. Em urgências, procure '
        'atendimento de saúde.</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="footer">FalaBula · versão 2.5 · Projeto acadêmico de inteligência artificial'
    ' · Informação responsável</div>',
    unsafe_allow_html=True,
)
