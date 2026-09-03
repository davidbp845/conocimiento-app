"""Implementación de GeneradorRespuestas y ClasificadorNotas sobre la
API de Anthropic. Fuerza tool_choice a una única tool con el schema
exacto que necesita RespuestaGenerada/SugerenciaClasificacion, en vez
de parsear texto libre — así un cambio de estilo en la respuesta del
modelo no puede romper el parseo."""
from __future__ import annotations

import os

from anthropic import Anthropic

from application.prompts import PROMPT_GENERADOR, PROMPT_RESUMIDOR, prompt_clasificador
from domain.entities import Nota, RespuestaGenerada, SugerenciaClasificacion
from domain.ports import ClasificadorNotas, GeneradorRespuestas

_MODELO_DEFECTO = "claude-sonnet-5"

_HERRAMIENTA_RESPUESTA = {
    "name": "publicar_respuesta",
    "description": "Publica la respuesta ya redactada en el formato que necesita la base de conocimiento.",
    "input_schema": {
        "type": "object",
        "properties": {
            "titulo": {"type": "string"},
            "contenido": {"type": "string", "description": "Cuerpo completo en Markdown."},
            "resumen": {"type": "string", "description": "Una sola frase."},
            "tags_sugeridas": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["titulo", "contenido", "resumen", "tags_sugeridas"],
    },
}

_HERRAMIENTA_CLASIFICACION = {
    "name": "clasificar_nota",
    "description": "Decide los tags definitivos y la carpeta destino (o null) para una nota.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}},
            "categoria": {"type": ["string", "null"]},
        },
        "required": ["tags", "categoria"],
    },
}


def _entrada_de_tool_use(mensaje, nombre_tool: str) -> dict:
    """El SDK no garantiza que el bloque de tool_use sea content[0]
    (podría haber texto antes); con tool_choice forzado a esta tool
    concreta siempre hay exactamente un bloque con ese nombre, pero lo
    buscamos en vez de asumir la posición."""
    for bloque in mensaje.content:
        if bloque.type == "tool_use" and bloque.name == nombre_tool:
            return bloque.input
    raise ValueError(f"La respuesta del modelo no incluyó la tool '{nombre_tool}' esperada.")


class GeneradorRespuestasAnthropic(GeneradorRespuestas):
    def __init__(self, modelo: str = _MODELO_DEFECTO, api_key: str | None = None):
        self._client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self._modelo = modelo

    def generar(self, pregunta: str) -> RespuestaGenerada:
        mensaje = self._client.messages.create(
            model=self._modelo,
            max_tokens=4096,
            system=PROMPT_GENERADOR,
            messages=[{"role": "user", "content": pregunta}],
            tools=[_HERRAMIENTA_RESPUESTA],
            tool_choice={"type": "tool", "name": "publicar_respuesta"},
        )
        entrada = _entrada_de_tool_use(mensaje, "publicar_respuesta")
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
        mensaje = self._client.messages.create(
            model=self._modelo,
            max_tokens=4096,
            system=PROMPT_RESUMIDOR,
            messages=[{"role": "user", "content": contenido}],
            tools=[_HERRAMIENTA_RESPUESTA],
            tool_choice={"type": "tool", "name": "publicar_respuesta"},
        )
        entrada = _entrada_de_tool_use(mensaje, "publicar_respuesta")
        return RespuestaGenerada(
            titulo=entrada["titulo"],
            contenido=entrada["contenido"],
            resumen=entrada.get("resumen"),
            tags_sugeridas=entrada.get("tags_sugeridas", []),
        )


class ClasificadorNotasAnthropic(ClasificadorNotas):
    def __init__(self, modelo: str = _MODELO_DEFECTO, api_key: str | None = None):
        self._client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self._modelo = modelo

    def clasificar(self, nota: Nota, categorias_existentes: list[str]) -> SugerenciaClasificacion:
        contenido_usuario = (
            f"Título: {nota.titulo}\n"
            f"Resumen: {nota.resumen or ''}\n"
            f"Tags actuales: {', '.join(nota.tags) or '(ninguno)'}\n\n"
            f"{nota.contenido}"
        )
        mensaje = self._client.messages.create(
            model=self._modelo,
            max_tokens=1024,
            system=prompt_clasificador(categorias_existentes),
            messages=[{"role": "user", "content": contenido_usuario}],
            tools=[_HERRAMIENTA_CLASIFICACION],
            tool_choice={"type": "tool", "name": "clasificar_nota"},
        )
        entrada = _entrada_de_tool_use(mensaje, "clasificar_nota")
        return SugerenciaClasificacion(tags=entrada.get("tags", []), categoria=entrada.get("categoria"))
