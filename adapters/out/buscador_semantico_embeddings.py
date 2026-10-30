"""Implementación de BuscadorSemantico con embeddings locales: un
vector por nota (título, resumen y contenido) y similitud coseno en
memoria contra el de la consulta. Sin base de datos vectorial: para
cientos de notas basta con recorrerlas todas.

El índice es un JSON en disco con el vector y un hash del texto de
cada nota. Se pone al día en cada búsqueda, no al guardar: el bot, el
timer de `normalizar` y las ediciones a mano escriben en vault_out/
desde otros procesos, así que solo comparando hashes al buscar queda
garantizado que el índice refleja lo que hay. Mover una nota no
cuesta nada (mismo id, mismo texto); cambiar de modelo lo reconstruye
entero.

`sentence-transformers` es una dependencia opcional
(requirements-semantica.txt): crear_buscador_semantico() devuelve None
si no está instalada, y quien lo construye usa entonces solo la
búsqueda literal."""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from pathlib import Path

from domain.entities import Nota
from domain.ports import BuscadorSemantico

# Multilingüe porque las notas están en español; pequeño (384
# dimensiones) para que funcione en CPU en el VPS.
MODELO_POR_DEFECTO = "paraphrase-multilingual-MiniLM-L12-v2"

# Similitud coseno mínima para dar una nota por relevante con
# MODELO_POR_DEFECTO. Con él, una paráfrasis de la nota buscada puntúa
# a partir de ~0.35 y una nota sin relación rara vez pasa de ~0.25;
# sin umbral, todas las notas saldrían en cualquier búsqueda.
UMBRAL_POR_DEFECTO = 0.3

Embedder = Callable[[list[str]], list[list[float]]]


class BuscadorSemanticoEmbeddings(BuscadorSemantico):
    def __init__(
        self,
        embedder: Embedder,
        ruta_indice: Path | str,
        modelo: str = MODELO_POR_DEFECTO,
        umbral: float = UMBRAL_POR_DEFECTO,
    ):
        self._embedder = embedder
        self._ruta_indice = Path(ruta_indice)
        self._modelo = modelo
        self._umbral = umbral

    def buscar(self, consulta: str, notas: list[Nota]) -> list[tuple[str, float]]:
        vectores = self._sincronizar(notas)
        consulta_vector = _normalizar(self._embedder([consulta])[0])
        puntuadas = [
            (nota.id, sum(a * b for a, b in zip(consulta_vector, vectores[nota.id], strict=True)))
            for nota in notas
        ]
        relevantes = [(nota_id, p) for nota_id, p in puntuadas if p >= self._umbral]
        return sorted(relevantes, key=lambda par: par[1], reverse=True)

    def _sincronizar(self, notas: list[Nota]) -> dict[str, list[float]]:
        """Pone el índice al día con `notas` y devuelve su vector por id.
        Solo calcula embeddings de las notas nuevas o cuyo texto cambió,
        y quita las que ya no están (borradas)."""
        indice = self._cargar_indice()
        textos = {nota.id: _texto_indexable(nota) for nota in notas}
        hashes = {nota_id: _hash(texto) for nota_id, texto in textos.items()}

        borradas = indice.keys() - textos.keys()
        for nota_id in borradas:
            del indice[nota_id]

        pendientes = [nota_id for nota_id, h in hashes.items() if indice.get(nota_id, {}).get("hash") != h]
        if pendientes:
            nuevos = self._embedder([textos[nota_id] for nota_id in pendientes])
            for nota_id, vector in zip(pendientes, nuevos, strict=True):
                indice[nota_id] = {"hash": hashes[nota_id], "vector": _normalizar(vector)}
        if pendientes or borradas:
            self._guardar_indice(indice)

        return {nota_id: indice[nota_id]["vector"] for nota_id in textos}

    def _cargar_indice(self) -> dict[str, dict]:
        try:
            datos = json.loads(self._ruta_indice.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        if datos.get("modelo") != self._modelo:
            return {}
        return datos.get("notas", {})

    def _guardar_indice(self, indice: dict[str, dict]) -> None:
        carpeta = self._ruta_indice.parent
        carpeta.mkdir(parents=True, exist_ok=True)
        # Mismo recurso que .pytest_cache: la carpeta se ignora a sí
        # misma, así el índice queda fuera de git tanto en este repo
        # como en el que lo embebe como submódulo.
        gitignore = carpeta / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*\n", encoding="utf-8")

        # Escritura atómica: el panel y la CLI pueden buscar a la vez.
        temporal = self._ruta_indice.with_suffix(".tmp")
        temporal.write_text(json.dumps({"modelo": self._modelo, "notas": indice}), encoding="utf-8")
        temporal.replace(self._ruta_indice)


def crear_buscador_semantico(vault_out: Path | str) -> BuscadorSemantico | None:
    """El buscador con sentence-transformers, o None si la dependencia
    opcional no está instalada. El índice vive junto al vault, en
    `<padre de vault_out>/.cache/indice_semantico.json`. El modelo se
    carga en la primera búsqueda, no aquí, para no frenar el arranque
    del panel ni de los subcomandos de la CLI que no buscan."""
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return None

    modelo_cargado = None

    def embedder(textos: list[str]) -> list[list[float]]:
        nonlocal modelo_cargado
        if modelo_cargado is None:
            from sentence_transformers import SentenceTransformer
            # CPU siempre: el modelo es pequeño, y un torch compilado sin
            # soporte para la GPU de la máquina falla al codificar
            # aunque la detecte.
            modelo_cargado = SentenceTransformer(MODELO_POR_DEFECTO, device="cpu")
        return modelo_cargado.encode(textos).tolist()

    return BuscadorSemanticoEmbeddings(embedder, Path(vault_out).parent / ".cache" / "indice_semantico.json")


def _texto_indexable(nota: Nota) -> str:
    # Título y resumen primero: el modelo trunca los textos largos, y
    # son lo que mejor dice de qué va la nota.
    return "\n".join(filter(None, [nota.titulo, nota.resumen, nota.contenido]))


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _normalizar(vector: list[float]) -> list[float]:
    norma = math.sqrt(sum(x * x for x in vector))
    return [x / norma for x in vector] if norma else list(vector)
