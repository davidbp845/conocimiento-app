"""Panel de visualización, búsqueda, chat y resumen de documentos/páginas
web de vault_out/. Lee/escribe directamente con
RepositorioNotasFilesystem — no pasa por ningún backend HTTP (ver
"streamlit_app/" en README.md: no reimplementa su propia búsqueda, reusa
BuscarNotas; el chat tampoco reimplementa la generación de respuestas,
reusa ResponderYArchivar igual que adapters/in_/telegram_bot.py; la
pestaña Documento reusa ResumirYArchivarDocumento y la pestaña Web
reusa ResumirYArchivarPaginaWeb)."""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

# Permite `streamlit run streamlit_app/app.py` desde la raíz del repo
# sin instalar el proyecto como paquete (mismo motivo que
# conftest.py para pytest).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

from adapters.out.repositorio_notas_filesystem import RepositorioNotasFilesystem
from config.paths import home
from domain.entities import FuenteNota
from domain.exceptions import ExtraccionTextoFallida, NotaNoExiste
from domain.use_cases import (
    BuscarNotas,
    EliminarNota,
    ResponderYArchivar,
    ResumirYArchivarDocumento,
    ResumirYArchivarPaginaWeb,
)

load_dotenv(home() / ".env")

st.set_page_config(page_title="Conocimiento", layout="centered")

# Nada de CSS inyectada vía st.markdown(unsafe_allow_html=True) aquí a
# propósito: cualquier llamada así es un elemento más de Streamlit
# colocado en el sitio del script donde se invoca (antes de
# st.title()), y ocupa brevemente el hueco por defecto de un elemento
# mientras el navegador termina de medir su contenido (invisible, solo
# un <style>) — eso es lo que provocaba el parpadeo por encima del
# título. El panel hermano panel_empleados/streamlit_app.py (del
# proyecto orquestador) tampoco inyecta CSS, solo toolbarMode="minimal"
# en .streamlit/config.toml.
#
# Probado también un <style> puntual tras st.title() solo para
# margin-top (id #conocimiento): mismo parpadeo (carga sin el margen y
# un instante después con él) aunque el valor sea fijo y no oculte
# nada — el problema es el <style> inyectado en sí, no lo que hace.


@st.cache_resource
def _repositorio() -> RepositorioNotasFilesystem:
    return RepositorioNotasFilesystem(os.environ.get("VAULT_OUT_PATH", str(home() / "vault_out")))


def _generador(proveedor: str):
    if proveedor == "mock":
        from adapters.out.llm_mock import GeneradorRespuestasMock
        return GeneradorRespuestasMock()
    if proveedor == "openai":
        from adapters.out.llm_openai import GeneradorRespuestasOpenAI
        return GeneradorRespuestasOpenAI()
    from adapters.out.llm_anthropic import GeneradorRespuestasAnthropic
    return GeneradorRespuestasAnthropic()


@st.cache_resource
def _responder(proveedor: str) -> ResponderYArchivar:
    return ResponderYArchivar(_generador(proveedor), _repositorio())


@st.cache_resource
def _resumidor(proveedor: str) -> ResumirYArchivarDocumento:
    from adapters.out.extractor_texto_pypdf import ExtractorTextoPypdf
    return ResumirYArchivarDocumento(ExtractorTextoPypdf(), _generador(proveedor), _repositorio())


@st.cache_resource
def _resumidor_web(proveedor: str) -> ResumirYArchivarPaginaWeb:
    from adapters.out.extractor_texto_web import ExtractorTextoWebHttp
    return ResumirYArchivarPaginaWeb(ExtractorTextoWebHttp(), _generador(proveedor), _repositorio())


st.title("Conocimiento")

tab_chat, tab_documento, tab_web, tab_buscar, tab_etiquetas, tab_readme = st.tabs(
    ["Chat", "Documento", "Web", "Buscar", "Etiquetas", "Readme"]
)

with tab_chat:
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    # PROVEEDOR_LLM=mock (ver .env.example) fuerza respuestas de prueba
    # sin llamar a ningún LLM real, sea cual sea el proveedor elegido
    # abajo — mismo criterio que main.py/cli.py para desarrollar sin
    # gastar tokens ni necesitar una API key.
    if os.environ.get("PROVEEDOR_LLM", "anthropic") == "mock":
        st.caption("PROVEEDOR_LLM=mock — respuestas de prueba, sin llamar a ningún LLM real.")
        proveedor = "mock"
    else:
        proveedor = st.selectbox(
            "Proveedor", ["OpenAI", "Anthropic"], key="proveedor_llm", label_visibility="collapsed"
        ).lower()

    conversacion = st.container(height=450)
    for pregunta, respuesta in st.session_state.mensajes:
        with conversacion:
            with st.chat_message("user"):
                st.markdown(pregunta)
            with st.chat_message("assistant"):
                st.markdown(respuesta)

    # No usamos st.chat_input a propósito: ese widget se ancla al fondo
    # del viewport (o de un container) mediante una posición que
    # Streamlit calcula por JS/CSS después del primer montaje, lo que
    # provoca un parpadeo visible al cargar (aparece un instante en su
    # posición natural, arriba, antes de saltar a la posición ancla).
    # Un formulario normal se coloca en su sitio del flujo del
    # documento desde el primer render, sin ese salto.
    with st.form("form_chat", clear_on_submit=True):
        col_pregunta, col_enviar = st.columns([5, 1])
        pregunta = col_pregunta.text_input(
            "Pregunta algo...", label_visibility="collapsed", placeholder="Pregunta algo..."
        )
        enviado = col_enviar.form_submit_button("Enviar")

    if enviado and pregunta:
        with conversacion:
            with st.chat_message("user"):
                st.markdown(pregunta)
            with st.chat_message("assistant"):
                with st.spinner("Generando respuesta..."):
                    try:
                        nota = _responder(proveedor).ejecutar(pregunta, FuenteNota.STREAMLIT)
                        respuesta = f"{nota.contenido}\n\n*(guardada como `{nota.id}`)*"
                    except Exception as e:
                        respuesta = f"No he podido generar la respuesta: {e}"
                st.markdown(respuesta)
        st.session_state.mensajes.append((pregunta, respuesta))

with tab_documento:
    if os.environ.get("PROVEEDOR_LLM", "anthropic") == "mock":
        st.caption("PROVEEDOR_LLM=mock — resumen de prueba, sin llamar a ningún LLM real.")
        proveedor_doc = "mock"
    else:
        proveedor_doc = st.selectbox(
            "Proveedor", ["OpenAI", "Anthropic"], key="proveedor_llm_documento", label_visibility="collapsed"
        ).lower()

    archivo = st.file_uploader("Sube un documento para resumir", type=["pdf", "txt", "md"])
    instruccion = st.text_input(
        "Pregunta algo sobre el documento...",
        label_visibility="collapsed",
        placeholder="Pregunta algo sobre el documento... (opcional, vacío = resumen)",
    )

    if archivo is not None and st.button("Resumir y archivar"):
        with st.spinner("Extrayendo texto y generando el resumen..."):
            try:
                nota = _resumidor(proveedor_doc).ejecutar(
                    archivo.getvalue(), archivo.name, FuenteNota.STREAMLIT, instruccion or None
                )
                st.success(f"Guardada como `{nota.id}`")
                st.markdown(nota.contenido)
            except ExtraccionTextoFallida as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"No he podido generar el resumen: {e}")

with tab_web:
    if os.environ.get("PROVEEDOR_LLM", "anthropic") == "mock":
        st.caption("PROVEEDOR_LLM=mock — resumen de prueba, sin llamar a ningún LLM real.")
        proveedor_web = "mock"
    else:
        proveedor_web = st.selectbox(
            "Proveedor", ["OpenAI", "Anthropic"], key="proveedor_llm_web", label_visibility="collapsed"
        ).lower()

    url = st.text_input("URL de la página", placeholder="https://...")
    instruccion_web = st.text_input(
        "Pregunta algo sobre la página...",
        label_visibility="collapsed",
        placeholder="Pregunta algo sobre la página... (opcional, vacío = resumen)",
    )

    if url and st.button("Resumir y archivar", key="resumir_web"):
        with st.spinner("Descargando la página y generando el resumen..."):
            try:
                nota = _resumidor_web(proveedor_web).ejecutar(
                    url, FuenteNota.STREAMLIT, instruccion_web or None
                )
                st.success(f"Guardada como `{nota.id}`")
                st.markdown(nota.contenido)
            except ExtraccionTextoFallida as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"No he podido generar el resumen: {e}")

with tab_buscar:
    col_texto, col_tag = st.columns([3, 1])
    texto = col_texto.text_input("Buscar", "")
    tag = col_tag.text_input("Tag", "")

    notas = BuscarNotas(_repositorio()).ejecutar(
        texto=texto or None,
        tags=[tag] if tag else None,
    )

    st.caption(f"{len(notas)} nota(s)")

    if "confirmar_eliminar" not in st.session_state:
        st.session_state.confirmar_eliminar = None

    for nota in sorted(notas, key=lambda n: n.creado_en, reverse=True):
        ruta = f"{nota.categoria}/{nota.id}" if nota.categoria else nota.id
        with st.expander(f"{nota.titulo}  ·  {ruta}"):
            if nota.resumen:
                st.caption(nota.resumen)
            if nota.tags:
                st.write(" ".join(f"`{t}`" for t in nota.tags))
            st.markdown(nota.contenido)

            # Confirmación en dos pasos para evitar borrados por
            # accidente: el primer clic solo marca la nota como
            # pendiente, el segundo (en un rerun aparte) la borra.
            if st.session_state.confirmar_eliminar == nota.id:
                st.warning(f"¿Eliminar «{nota.titulo}»? No se puede deshacer.")
                col_si, col_no = st.columns(2)
                if col_si.button("Sí, eliminar", key=f"confirmar_{nota.id}"):
                    try:
                        EliminarNota(_repositorio()).ejecutar(nota.id)
                    except NotaNoExiste:
                        st.error("La nota ya no existe (¿borrada desde otro sitio?).")
                    st.session_state.confirmar_eliminar = None
                    st.rerun()
                if col_no.button("Cancelar", key=f"cancelar_{nota.id}"):
                    st.session_state.confirmar_eliminar = None
                    st.rerun()
            elif st.button("Eliminar nota", key=f"eliminar_{nota.id}"):
                st.session_state.confirmar_eliminar = nota.id
                st.rerun()

with tab_etiquetas:
    notas_todas = BuscarNotas(_repositorio()).ejecutar()
    conteo = Counter(t for nota in notas_todas for t in nota.tags)

    if not conteo:
        st.caption("Todavía no hay etiquetas — aparecerán aquí en cuanto se archive alguna nota con tags.")
    else:
        # Sin HTML/CSS a mano: mismo motivo que el resto del panel no
        # inyecta CSS vía st.markdown(unsafe_allow_html) — provoca
        # parpadeo al cargar (ver comentario más arriba). Para un
        # tamaño real (h1..h6) hace falta Markdown de bloque, que
        # st.pills escapa a texto literal en sus labels (confirmado en
        # el código de Streamlit) — por eso el tamaño va en un bloque
        # de solo lectura aparte, y los pills de abajo, ya sin variar
        # de tamaño, son solo el control para filtrar por etiqueta.
        etiquetas_ordenadas = sorted(conteo)
        maximo, minimo = max(conteo.values()), min(conteo.values())
        rango = maximo - minimo

        def _nivel(etiqueta: str) -> int:
            if rango == 0:
                return 3
            ratio = (conteo[etiqueta] - minimo) / rango
            return 6 - round(ratio * 5)  # 1 (h1, más notas) .. 6 (h6, menos)

        por_nivel: dict[int, list[str]] = {n: [] for n in range(1, 7)}
        for t in etiquetas_ordenadas:
            por_nivel[_nivel(t)].append(t)

        for nivel in range(1, 7):
            tags_nivel = por_nivel[nivel]
            if tags_nivel:
                st.markdown(f"{'#' * nivel} " + " · ".join(f"{t} ({conteo[t]})" for t in tags_nivel))

        st.divider()
        etiqueta = st.pills(
            "Filtrar por etiqueta",
            etiquetas_ordenadas,
            format_func=lambda t: f"{t} ({conteo[t]})",
        )

        if etiqueta:
            notas_tag = [n for n in notas_todas if etiqueta in n.tags]
            st.caption(f"{len(notas_tag)} nota(s) con «{etiqueta}»")
            for nota in sorted(notas_tag, key=lambda n: n.creado_en, reverse=True):
                ruta = f"{nota.categoria}/{nota.id}" if nota.categoria else nota.id
                with st.expander(f"{nota.titulo}  ·  {ruta}"):
                    if nota.resumen:
                        st.caption(nota.resumen)
                    st.write(" ".join(f"`{t}`" for t in nota.tags))
                    st.markdown(nota.contenido)

with tab_readme:
    # README.md de la raíz del vault en uso (home(): la del propio
    # conocimiento_app en modo standalone, o la del repo que lo embebe
    # si exporta CONOCIMIENTO_HOME — ver config/paths.py). st.markdown
    # sin unsafe_allow_html: es Markdown plano, sin <style>/HTML, así
    # que no aplica el problema de parpadeo documentado más arriba.
    _readme = home() / "README.md"
    if _readme.exists():
        st.markdown(_readme.read_text(encoding="utf-8"))
    else:
        st.caption("No se encuentra README.md en la raíz del proyecto.")
