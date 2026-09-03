"""
Casos de uso: orquestan entidades y puertos para resolver una acción
concreta (archivar una respuesta, buscarla, reorganizar el árbol de
vault_out). Esto es lo que invocan los adaptadores de entrada
(adapters/in_/telegram_bot.py, adapters/in_/cli.py) — nunca al revés.
"""
from __future__ import annotations

from .entities import FuenteNota, Movimiento, Nota
from .ports import ClasificadorNotas, ExtractorTexto, ExtractorTextoWeb, GeneradorRespuestas, RepositorioNotas

# Nº mínimo de notas afines que debe reunir una categoría nueva antes de
# crearla — regla 2 de "Crecimiento del árbol" en README.md. Evita ramas
# con uno o dos ficheros.
UMBRAL_MINIMO_NOTAS_POR_CATEGORIA = 5

# Niveles máximos de profundidad de una categoria ("git/commits" = 2) —
# regla 4 de "Crecimiento del árbol" en README.md.
PROFUNDIDAD_MAXIMA_CATEGORIA = 2


class ResponderYArchivar:
    """Pregunta entrante (Telegram o CLI) -> respuesta del LLM -> Nota
    nueva, guardada plana en la raíz de vault_out (sin categoria). La
    clasificación en subcarpetas es cosa aparte, de
    PlanificarReorganizacion/AplicarReorganizacion más abajo — este
    caso de uso no la decide."""

    def __init__(self, generador: GeneradorRespuestas, notas: RepositorioNotas):
        self._generador = generador
        self._notas = notas

    def ejecutar(self, pregunta: str, fuente: FuenteNota) -> Nota:
        respuesta = self._generador.generar(pregunta)
        nota = Nota.nueva(
            titulo=respuesta.titulo,
            contenido=respuesta.contenido,
            fuente=fuente,
            tags=respuesta.tags_sugeridas,
            pregunta_origen=pregunta,
            resumen=respuesta.resumen,
        )
        self._notas.guardar(nota)
        return nota


class ArchivarNotaRedactada:
    """Para cuando la nota ya viene redactada de fuera (p. ej. una
    sesión de Claude Code que escribe directamente el markdown) y no
    hace falta pasar por GeneradorRespuestas — es lo que usa
    `adapters/in_/cli.py guardar`. fuente es siempre CLAUDE_CODE: si en
    el futuro hace falta archivar contenido ya redactado desde otro
    origen, se añade un parámetro entonces, no antes."""

    def __init__(self, notas: RepositorioNotas):
        self._notas = notas

    def ejecutar(
        self,
        titulo: str,
        contenido: str,
        tags: list[str] | None = None,
        pregunta_origen: str | None = None,
        resumen: str | None = None,
    ) -> Nota:
        nota = Nota.nueva(
            titulo=titulo,
            contenido=contenido,
            fuente=FuenteNota.CLAUDE_CODE,
            tags=tags,
            pregunta_origen=pregunta_origen,
            resumen=resumen,
        )
        self._notas.guardar(nota)
        return nota


class ResumirYArchivarDocumento:
    """Documento subido (PDF, .txt, .md) -> texto extraído -> resumen del
    LLM -> Nota nueva, guardada plana en la raíz de vault_out (sin
    categoria). Mismo patrón que ResponderYArchivar pero partiendo de un
    fichero en vez de una pregunta."""

    def __init__(self, extractor: ExtractorTexto, generador: GeneradorRespuestas, notas: RepositorioNotas):
        self._extractor = extractor
        self._generador = generador
        self._notas = notas

    def ejecutar(
        self, contenido: bytes, nombre_archivo: str, fuente: FuenteNota, instruccion: str | None = None
    ) -> Nota:
        texto = self._extractor.extraer(contenido, nombre_archivo)
        respuesta = self._generador.resumir(texto, nombre_archivo, instruccion)
        pregunta_origen = (
            f"{instruccion} (documento «{nombre_archivo}»)"
            if instruccion
            else f"Resumen del documento «{nombre_archivo}»"
        )
        nota = Nota.nueva(
            titulo=respuesta.titulo,
            contenido=respuesta.contenido,
            fuente=fuente,
            tags=respuesta.tags_sugeridas,
            pregunta_origen=pregunta_origen,
            resumen=respuesta.resumen,
        )
        self._notas.guardar(nota)
        return nota


class ResumirYArchivarPaginaWeb:
    """URL de una página web -> texto extraído -> resumen del LLM ->
    Nota nueva, guardada plana en la raíz de vault_out (sin categoria).
    Mismo patrón que ResumirYArchivarDocumento pero partiendo de una
    URL en vez de un fichero subido."""

    def __init__(self, extractor: ExtractorTextoWeb, generador: GeneradorRespuestas, notas: RepositorioNotas):
        self._extractor = extractor
        self._generador = generador
        self._notas = notas

    def ejecutar(self, url: str, fuente: FuenteNota, instruccion: str | None = None) -> Nota:
        texto = self._extractor.extraer(url)
        respuesta = self._generador.resumir(texto, url, instruccion)
        pregunta_origen = f"{instruccion} (página «{url}»)" if instruccion else f"Resumen de la página «{url}»"
        nota = Nota.nueva(
            titulo=respuesta.titulo,
            contenido=respuesta.contenido,
            fuente=fuente,
            tags=respuesta.tags_sugeridas,
            pregunta_origen=pregunta_origen,
            resumen=respuesta.resumen,
        )
        self._notas.guardar(nota)
        return nota


class BuscarNotas:
    """Delega en RepositorioNotas.buscar. Lo usan tanto
    `adapters/in_/cli.py buscar` como el panel Streamlit — sin lógica
    de dominio propia más allá de la ya descrita en el puerto (ver
    domain/ports.py), para que ambos consumidores busquen siempre
    igual."""

    def __init__(self, notas: RepositorioNotas):
        self._notas = notas

    def ejecutar(self, texto: str | None = None, tags: list[str] | None = None) -> list[Nota]:
        return self._notas.buscar(texto=texto, tags=tags)


class EliminarNota:
    """Borra una nota por id, delegando en RepositorioNotas.eliminar
    (irreversible). La usa el panel Streamlit para quitar duplicados
    (p. ej. una misma pregunta archivada dos veces) uno a uno — sin
    lógica de dominio propia más allá de propagar NotaNoExiste si el
    id no existe."""

    def __init__(self, notas: RepositorioNotas):
        self._notas = notas

    def ejecutar(self, nota_id: str) -> None:
        self._notas.eliminar(nota_id)


def _profundidad(categoria: str) -> int:
    """'git' -> 1, 'git/commits' -> 2."""
    return categoria.count("/") + 1


class PlanificarReorganizacion:
    """Calcula el plan de movimientos para el comando `reorganizar`
    (dry-run por defecto, regla 5 en README.md) sin tocar vault_out.
    Solo considera notas todavía sin categoria (categoria is None) —
    una nota ya clasificada no se reconsidera en pasadas posteriores,
    para que el árbol no cambie de sitio solo mediante volver a
    ejecutar el comando (ver regla 1: una nota, una carpeta)."""

    def __init__(
        self,
        notas: RepositorioNotas,
        clasificador: ClasificadorNotas,
        umbral_minimo: int = UMBRAL_MINIMO_NOTAS_POR_CATEGORIA,
        profundidad_maxima: int = PROFUNDIDAD_MAXIMA_CATEGORIA,
    ):
        self._notas = notas
        self._clasificador = clasificador
        self._umbral_minimo = umbral_minimo
        self._profundidad_maxima = profundidad_maxima

    def ejecutar(self) -> list[Movimiento]:
        categorias_existentes = self._notas.listar_categorias()
        pendientes = [n for n in self._notas.listar() if n.categoria is None]

        movimientos: list[Movimiento] = []
        # Categorías todavía inexistentes candidatas a crearse en esta
        # pasada: solo se confirman si reúnen el umbral mínimo de notas
        # (regla 2) — hasta entonces sus notas se quedan planas.
        candidatas_nuevas: dict[str, list[Nota]] = {}

        for nota in pendientes:
            sugerencia = self._clasificador.clasificar(nota, categorias_existentes)
            if sugerencia.categoria is None:
                continue
            if _profundidad(sugerencia.categoria) > self._profundidad_maxima:
                continue
            if sugerencia.categoria in categorias_existentes:
                # Ampliar una carpeta que ya existe no necesita umbral:
                # ya está justificada (regla 3).
                movimientos.append(Movimiento(nota.id, nota.categoria, sugerencia.categoria))
            else:
                candidatas_nuevas.setdefault(sugerencia.categoria, []).append(nota)

        for categoria, notas_candidatas in candidatas_nuevas.items():
            if len(notas_candidatas) < self._umbral_minimo:
                continue
            movimientos.extend(
                Movimiento(n.id, n.categoria, categoria) for n in notas_candidatas
            )

        return movimientos


class AplicarReorganizacion:
    """Ejecuta un plan ya calculado por PlanificarReorganizacion. No
    vuelve a planificar nada — separar "calcular" de "aplicar" es lo
    que permite el dry-run del comando `reorganizar` (regla 5 en
    README.md); `--aplicar` es lo único que llama a este caso de uso."""

    def __init__(self, notas: RepositorioNotas):
        self._notas = notas

    def ejecutar(self, plan: list[Movimiento]) -> None:
        for movimiento in plan:
            self._notas.mover(movimiento.nota_id, movimiento.categoria_propuesta)
