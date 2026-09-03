"""
Puertos: contratos que el dominio necesita y que los adaptadores
implementan. El dominio depende de estas interfaces, nunca de una
implementación concreta (ficheros locales, Anthropic, Telegram...).

Esto es lo que permite sustituir el repositorio de notas o el LLM sin
tocar domain/ ni application/ — ver "Cómo sustituir un adaptador" en
README.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .entities import Nota, NotaNormalizada, RespuestaGenerada, SugerenciaClasificacion

# ---------- Puertos de salida: persistencia ----------

class RepositorioNotas(ABC):
    """Lee/escribe las notas de vault_out/. La implementación prevista
    es de ficheros locales (adapters/out/repositorio_notas_filesystem.py,
    un .md con frontmatter por Nota), pero el dominio no lo sabe."""

    @abstractmethod
    def guardar(self, nota: Nota) -> None:
        """Crea la nota si no existe, o la sobrescribe si ya había una
        con el mismo id. mover() es la única vía prevista para cambiar
        la categoria de una nota ya guardada, no guardar() con
        categoria distinta — evita que dos rutas queden apuntando al
        mismo id si la implementación no mueve el fichero de forma
        atómica."""
        ...

    @abstractmethod
    def obtener(self, nota_id: str) -> Nota | None: ...

    @abstractmethod
    def listar(self) -> list[Nota]: ...

    @abstractmethod
    def buscar(self, texto: str | None = None, tags: list[str] | None = None) -> list[Nota]:
        """texto busca en titulo/contenido/resumen; tags filtra por
        coincidencia exacta (AND entre varios tags). Ambos en None
        equivale a listar(). Lo usan tanto la CLI (`buscar`) como el
        panel Streamlit."""
        ...

    @abstractmethod
    def listar_categorias(self) -> list[str]:
        """Todas las carpetas que ya existen bajo vault_out (rutas
        relativas), para que ClasificadorNotas y el planificador de
        reorganización puedan priorizar reusar una existente en vez de
        crear una nueva (regla 3 de "Crecimiento del árbol" en
        README.md)."""
        ...

    @abstractmethod
    def mover(self, nota_id: str, nueva_categoria: str | None) -> None:
        """Reubica el fichero físico de la nota y actualiza su
        categoria. nueva_categoria=None la devuelve a la raíz de
        vault_out. Única forma prevista de cambiar la categoria de una
        nota ya guardada — la usa `reorganizar --aplicar`. Lanza
        NotaNoExiste (domain/exceptions.py) si nota_id no existe."""
        ...

    @abstractmethod
    def eliminar(self, nota_id: str) -> None:
        """Borra el fichero físico de la nota (p. ej. una duplicada por
        una petición hecha dos veces). Irreversible: no hay papelera ni
        confirmación a este nivel — eso es cosa del adaptador de
        entrada (el panel Streamlit pide confirmación antes de llamar
        aquí). Lanza NotaNoExiste (domain/exceptions.py) si nota_id no
        existe."""
        ...


# ---------- Puertos de salida: IA ----------

class GeneradorRespuestas(ABC):
    """Adaptador hacia el LLM que redacta la respuesta tipo tutorial a
    una pregunta entrante (Telegram o CLI), o el resumen de un documento
    ya extraído (panel Streamlit, ver ExtractorTexto más abajo)."""

    @abstractmethod
    def generar(self, pregunta: str) -> RespuestaGenerada: ...

    @abstractmethod
    def resumir(self, texto: str, nombre_archivo: str, instruccion: str | None = None) -> RespuestaGenerada:
        """Como generar(), pero a partir del texto ya extraído de un
        documento (ver ExtractorTexto) en vez de una pregunta — misma
        salida, prompt distinto (application/prompts.py). instruccion
        es opcional: si se da, sustituye el resumen genérico por defecto
        (p. ej. "extrae las fechas clave", "tradúcelo al inglés")."""
        ...


class ClasificadorNotas(ABC):
    """Sugiere tags y carpeta destino para una nota ya redactada, dado
    el árbol de categorías que ya existe en vault_out. No decide por
    sí mismo si aplicar la sugerencia — eso lo hacen las reglas de
    domain/use_cases.py (umbral mínimo, profundidad máxima, ver
    "Crecimiento del árbol" en README.md), que pueden descartarla."""

    @abstractmethod
    def clasificar(self, nota: Nota, categorias_existentes: list[str]) -> SugerenciaClasificacion: ...


class NormalizadorVaultIn(ABC):
    """Convierte el contenido crudo de un fichero de vault_in/ (sin
    frontmatter, a veces aplanado por un copia-pega desde Telegram) en
    una o varias NotaNormalizada listas para archivar en vault_out/ —
    normalmente una, más de una solo si el texto mezclaba temas
    realmente distintos que no deberían vivir en la misma nota. Lo usa
    `adapters/in_/cli.py normalizar`, la versión automatizable (sin
    Claude Code de por medio) de `/normalizar-vault-in`."""

    @abstractmethod
    def normalizar(self, texto_crudo: str) -> list[NotaNormalizada]: ...


# ---------- Puertos de salida: extracción de texto ----------

class ExtractorTexto(ABC):
    """Extrae texto plano de un fichero subido (PDF, .txt, .md...) para
    poder pasarlo al LLM que lo resume (GeneradorRespuestas.resumir). La
    implementación prevista es adapters/out/extractor_texto_pypdf.py,
    pero el dominio no lo sabe."""

    @abstractmethod
    def extraer(self, contenido: bytes, nombre_archivo: str) -> str:
        """Lanza ExtraccionTextoFallida (domain/exceptions.py) si el
        fichero no tiene texto extraíble (p.ej. un PDF escaneado sin
        OCR) o el tipo no está soportado."""
        ...


class ExtractorTextoWeb(ABC):
    """Descarga una página web y extrae su texto visible para poder
    pasarlo al LLM que lo resume (GeneradorRespuestas.resumir) — mismo
    puerto de salida que ExtractorTexto, pero partiendo de una URL en
    vez de un fichero ya subido. La implementación prevista es
    adapters/out/extractor_texto_web.py, pero el dominio no lo sabe."""

    @abstractmethod
    def extraer(self, url: str) -> str:
        """Lanza ExtraccionTextoFallida (domain/exceptions.py) si la
        URL no es alcanzable (red, timeout, estado HTTP de error) o la
        página no tiene texto extraíble."""
        ...
