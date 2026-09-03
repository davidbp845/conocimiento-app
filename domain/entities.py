"""
Entidades del dominio. Puro Python, sin dependencias de frameworks,
LLMs, bots de Telegram ni Streamlit. Esto es lo único que de verdad
define qué es una nota y cómo se identifica — el resto (cómo se genera
el texto, cómo se persiste el fichero) es adaptador.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class FuenteNota(StrEnum):
    TELEGRAM = "telegram"
    CLI = "cli"
    CLAUDE_CODE = "claude_code"
    STREAMLIT = "streamlit"
    # Un .md pegado a mano en vault_in/ y normalizado por
    # /normalizar-vault-in (ver .claude/commands/) — a diferencia de
    # CLAUDE_CODE, aquí no hay ninguna sesión redactando el contenido,
    # solo completando el frontmatter que faltaba.
    MANUAL = "manual"


def slug(texto: str, longitud_maxima: int = 60) -> str:
    """Convierte un título en un id de fichero estable: minúsculas,
    sin acentos, palabras separadas por guiones. Es el id de la nota
    (Nota.id) y no cambia después de creada — así mover() puede
    reubicar el fichero sin perder su identidad aunque categoria o
    tags cambien."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    con_guiones = re.sub(r"[^a-z0-9]+", "-", sin_acentos.lower()).strip("-")
    return con_guiones[:longitud_maxima].rstrip("-") or "nota"


@dataclass
class Nota:
    """Una respuesta archivada: el contenido de vault_out/*.md, sin el
    frontmatter (eso lo serializa RepositorioNotas). id es un slug
    derivado del título en el momento de crearla (ver Nota.nueva) y no
    cambia después — es la clave estable con la que RepositorioNotas
    localiza/mueve el fichero, aunque categoria o tags cambien."""
    id: str
    titulo: str
    contenido: str
    fuente: FuenteNota
    tags: list[str] = field(default_factory=list)
    # Ruta relativa dentro de vault_out (sin el nombre de fichero), p.ej.
    # "git/commits". None mientras la nota vive plana en la raíz, a la
    # espera de que el comando "reorganizar" le asigne una (ver regla 2
    # de "Crecimiento del árbol" en README.md).
    categoria: str | None = None
    pregunta_origen: str | None = None
    resumen: str | None = None
    # Granularidad de día, no de instante: es lo que se persiste en el
    # frontmatter (`fecha: AAAA-MM-DD`, ver README.md) y lo único que
    # importa para una nota de este tipo ("¿cuándo la escribí?").
    creado_en: date = field(default_factory=date.today)

    @staticmethod
    def nueva(
        titulo: str,
        contenido: str,
        fuente: FuenteNota,
        tags: list[str] | None = None,
        pregunta_origen: str | None = None,
        resumen: str | None = None,
    ) -> Nota:
        return Nota(
            id=slug(titulo),
            titulo=titulo,
            contenido=contenido,
            fuente=fuente,
            tags=tags or [],
            pregunta_origen=pregunta_origen,
            resumen=resumen,
        )


@dataclass
class RespuestaGenerada:
    """Lo que devuelve GeneradorRespuestas (puerto de salida hacia el
    LLM): el contenido de una posible nota, todavía sin id ni
    categoria — eso lo decide el caso de uso que la convierte en Nota
    vía Nota.nueva()."""
    titulo: str
    contenido: str
    resumen: str | None = None
    tags_sugeridas: list[str] = field(default_factory=list)


@dataclass
class NotaNormalizada:
    """Lo que devuelve NormalizadorVaultIn a partir del contenido crudo
    de un fichero de vault_in/: una posible nota, todavía sin id (lo
    decide Nota.nueva()) ni categoria (siempre None hasta que
    "reorganizar" la asigne, igual que el resto de fuentes de
    entrada). pregunta_origen puede ser una reconstrucción del propio
    normalizador, nunca la pregunta real tecleada por nadie — ver
    application/prompts.py:PROMPT_NORMALIZADOR."""
    titulo: str
    contenido: str
    tags: list[str] = field(default_factory=list)
    resumen: str | None = None
    pregunta_origen: str | None = None


@dataclass
class SugerenciaClasificacion:
    """Lo que devuelve ClasificadorNotas para una nota ya existente:
    tags definitivas y la carpeta donde debería vivir dentro de
    vault_out. categoria=None significa "que siga en la raíz" (p. ej.
    si el tema no tiene aún contenido suficiente para justificar una
    carpeta propia, ver regla 2 en README.md)."""
    tags: list[str]
    categoria: str | None


@dataclass
class Movimiento:
    """Un paso del plan que produce la reorganización: mover nota_id
    de categoria_actual a categoria_propuesta. Es la unidad que se
    muestra en el dry-run del comando `reorganizar` antes de
    aplicarse (ver domain/use_cases.py, pendiente de implementar)."""
    nota_id: str
    categoria_actual: str | None
    categoria_propuesta: str | None
