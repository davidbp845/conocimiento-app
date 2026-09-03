"""Implementaciones heurísticas de GeneradorRespuestas,
ClasificadorNotas y NormalizadorVaultIn para desarrollar/probar sin
gastar tokens ni necesitar ANTHROPIC_API_KEY (PROVEEDOR_LLM=mock, ver
.env.example)."""
from __future__ import annotations

import re
from pathlib import Path

from domain.entities import Nota, NotaNormalizada, RespuestaGenerada, SugerenciaClasificacion
from domain.ports import ClasificadorNotas, GeneradorRespuestas, NormalizadorVaultIn

_PALABRA = re.compile(r"[a-záéíóúñ0-9]+", re.IGNORECASE)
_PALABRAS_VACIAS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "que",
    "como", "cómo", "para", "por", "con", "se", "es", "del", "al", "sin",
}


class GeneradorRespuestasMock(GeneradorRespuestas):
    """No llama a ningún LLM: devuelve una respuesta de relleno,
    marcada como tal, a partir de la propia pregunta. Sirve para
    probar el resto del flujo (guardar, buscar, reorganizar) sin
    depender de la red ni de una API key."""

    def generar(self, pregunta: str) -> RespuestaGenerada:
        titulo = pregunta.strip().rstrip("?¿!¡.").capitalize()[:80] or "Nota sin título"
        return RespuestaGenerada(
            titulo=titulo,
            contenido=(
                "> Respuesta de PROVEEDOR_LLM=mock, sin contenido real.\n\n"
                f"Pregunta original: {pregunta}"
            ),
            resumen="Respuesta de prueba generada por el proveedor mock.",
            tags_sugeridas=_palabras_clave(pregunta),
        )

    def resumir(self, texto: str, nombre_archivo: str, instruccion: str | None = None) -> RespuestaGenerada:
        titulo = Path(nombre_archivo).stem.replace("_", " ").replace("-", " ").capitalize()[:80]
        instruccion_linea = f"Instrucción: {instruccion}\n\n" if instruccion else ""
        return RespuestaGenerada(
            titulo=titulo or "Documento sin título",
            contenido=(
                "> Resumen de PROVEEDOR_LLM=mock, sin contenido real.\n\n"
                f"{instruccion_linea}"
                f"Origen: {nombre_archivo}\n\n"
                f"Longitud del texto extraído: {len(texto)} caracteres."
            ),
            resumen="Resumen de prueba generado por el proveedor mock.",
            tags_sugeridas=_palabras_clave(texto),
        )


class ClasificadorNotasMock(ClasificadorNotas):
    """Nunca propone una categoria nueva ni una ya existente —
    deliberadamente conservador, para que ejecutar `reorganizar` en
    local con PROVEEDOR_LLM=mock nunca reorganice el vault de verdad
    por accidente. Conserva los tags que ya traía la nota, sin más."""

    def clasificar(self, nota: Nota, categorias_existentes: list[str]) -> SugerenciaClasificacion:
        return SugerenciaClasificacion(tags=nota.tags, categoria=None)


class NormalizadorVaultInMock(NormalizadorVaultIn):
    """No llama a ningún LLM ni reformatea nada: devuelve el texto tal
    cual como una única nota, con título/tags heurísticos — nunca
    detecta aplanado ni separa temas (eso exige de verdad entender el
    contenido). Sirve para probar el resto del flujo de `normalizar`
    (leer vault_in/, archivar, borrar el original) sin depender de la
    red ni de una API key."""

    def normalizar(self, texto_crudo: str) -> list[NotaNormalizada]:
        primera_linea = next((linea.strip() for linea in texto_crudo.splitlines() if linea.strip()), "")
        titulo = primera_linea.lstrip("#").strip().capitalize()[:80] or "Nota sin título"
        return [
            NotaNormalizada(
                titulo=titulo,
                contenido=(
                    "> Normalización de PROVEEDOR_LLM=mock, sin reformatear el contenido real.\n\n"
                    f"{texto_crudo}"
                ),
                tags=_palabras_clave(texto_crudo),
                resumen="Nota de prueba generada por el proveedor mock.",
                pregunta_origen=None,
            )
        ]


def _palabras_clave(texto: str, maximo: int = 3) -> list[str]:
    vistas: list[str] = []
    for palabra in _PALABRA.findall(texto.lower()):
        # <= 2 y no <= 3: términos técnicos de 3 letras ("git", "cli",
        # "ssh"...) son justo el tipo de tag útil que este mock debería
        # poder sugerir en un vault de tutoriales de desarrollo.
        if len(palabra) <= 2 or palabra in _PALABRAS_VACIAS or palabra in vistas:
            continue
        vistas.append(palabra)
        if len(vistas) == maximo:
            break
    return vistas
