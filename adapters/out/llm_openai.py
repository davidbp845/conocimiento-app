"""Implementación de GeneradorRespuestas sobre la API de OpenAI —
alternativa a llm_anthropic.py seleccionable desde la pestaña Chat del
panel Streamlit (ver streamlit_app/app.py). Mismo criterio que
llm_anthropic.py: fuerza tool_choice a una única function con el
schema exacto de RespuestaGenerada, en vez de parsear texto libre.
Solo implementa GeneradorRespuestas (no ClasificadorNotas) porque el
selector de proveedor vive únicamente en el chat — `reorganizar` sigue
usando el proveedor de PROVEEDOR_LLM (ver main.py/cli.py)."""
from __future__ import annotations

import json
import os

from openai import OpenAI

from application.prompts import PROMPT_GENERADOR, PROMPT_RESUMIDOR
from domain.entities import RespuestaGenerada
from domain.ports import GeneradorRespuestas

_MODELO_DEFECTO = "gpt-5"

_HERRAMIENTA_RESPUESTA = {
    "type": "function",
    "function": {
        "name": "publicar_respuesta",
        "description": "Publica la respuesta ya redactada en el formato que necesita la base de conocimiento.",
        "parameters": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string"},
                "contenido": {"type": "string", "description": "Cuerpo completo en Markdown."},
                "resumen": {"type": "string", "description": "Una sola frase."},
                "tags_sugeridas": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["titulo", "contenido", "resumen", "tags_sugeridas"],
        },
    },
}


class GeneradorRespuestasOpenAI(GeneradorRespuestas):
    def __init__(self, modelo: str = _MODELO_DEFECTO, api_key: str | None = None):
        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self._modelo = modelo

    def generar(self, pregunta: str) -> RespuestaGenerada:
        respuesta = self._client.chat.completions.create(
            model=self._modelo,
            messages=[
                {"role": "system", "content": PROMPT_GENERADOR},
                {"role": "user", "content": pregunta},
            ],
            tools=[_HERRAMIENTA_RESPUESTA],
            tool_choice={"type": "function", "function": {"name": "publicar_respuesta"}},
        )
        llamada = respuesta.choices[0].message.tool_calls[0]
        entrada = json.loads(llamada.function.arguments)
        return RespuestaGenerada(
            titulo=entrada["titulo"],
            contenido=entrada["contenido"],
            resumen=entrada.get("resumen"),
            tags_sugeridas=entrada.get("tags_sugeridas", []),
        )

    def resumir(self, texto: str, nombre_archivo: str, instruccion: str | None = None) -> RespuestaGenerada:
        contenido = f"Origen: {nombre_archivo}\n\n{texto}"
        if instruccion:
            contenido = f"Instrucción: {instruccion}\n\n{contenido}"
        respuesta = self._client.chat.completions.create(
            model=self._modelo,
            messages=[
                {"role": "system", "content": PROMPT_RESUMIDOR},
                {"role": "user", "content": contenido},
            ],
            tools=[_HERRAMIENTA_RESPUESTA],
            tool_choice={"type": "function", "function": {"name": "publicar_respuesta"}},
        )
        llamada = respuesta.choices[0].message.tool_calls[0]
        entrada = json.loads(llamada.function.arguments)
        return RespuestaGenerada(
            titulo=entrada["titulo"],
            contenido=entrada["contenido"],
            resumen=entrada.get("resumen"),
            tags_sugeridas=entrada.get("tags_sugeridas", []),
        )
