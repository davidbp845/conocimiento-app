"""Implementación de RepositorioNotas sobre ficheros locales: cada
Nota es un fichero <categoria>/<id>.md dentro de vault_out/, con el
frontmatter YAML documentado en README.md. id no se guarda en el
frontmatter — es el nombre del fichero sin extensión."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import frontmatter

from domain.entities import FuenteNota, Nota
from domain.exceptions import NotaNoExiste
from domain.ports import RepositorioNotas


class RepositorioNotasFilesystem(RepositorioNotas):
    def __init__(self, raiz: Path | str):
        self._raiz = Path(raiz)
        self._raiz.mkdir(parents=True, exist_ok=True)

    def guardar(self, nota: Nota) -> None:
        ruta = self._ruta_de(nota.id, nota.categoria)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(frontmatter.dumps(self._a_post(nota)).encode("utf-8"))

    def obtener(self, nota_id: str) -> Nota | None:
        ruta = self._buscar_fichero(nota_id)
        return self._leer(ruta) if ruta is not None else None

    def listar(self) -> list[Nota]:
        return [self._leer(ruta) for ruta in sorted(self._raiz.rglob("*.md"))]

    def buscar(self, texto: str | None = None, tags: list[str] | None = None) -> list[Nota]:
        notas = self.listar()
        if texto:
            clave = texto.lower()
            notas = [n for n in notas if clave in _texto_buscable(n)]
        if tags:
            requeridos = set(tags)
            notas = [n for n in notas if requeridos <= set(n.tags)]
        return notas

    def listar_categorias(self) -> list[str]:
        categorias = {
            ruta.relative_to(self._raiz).parent.as_posix()
            for ruta in self._raiz.rglob("*.md")
            if ruta.parent != self._raiz
        }
        return sorted(categorias)

    def mover(self, nota_id: str, nueva_categoria: str | None) -> None:
        ruta_actual = self._buscar_fichero(nota_id)
        if ruta_actual is None:
            raise NotaNoExiste(nota_id)

        nota = self._leer(ruta_actual)
        if nota.categoria == nueva_categoria:
            return

        nota.categoria = nueva_categoria
        nueva_ruta = self._ruta_de(nota.id, nueva_categoria)
        nueva_ruta.parent.mkdir(parents=True, exist_ok=True)
        nueva_ruta.write_bytes(frontmatter.dumps(self._a_post(nota)).encode("utf-8"))

        carpeta_antigua = ruta_actual.parent
        ruta_actual.unlink()
        self._limpiar_carpetas_vacias(carpeta_antigua)

    def eliminar(self, nota_id: str) -> None:
        ruta = self._buscar_fichero(nota_id)
        if ruta is None:
            raise NotaNoExiste(nota_id)

        carpeta = ruta.parent
        ruta.unlink()
        self._limpiar_carpetas_vacias(carpeta)

    def _ruta_de(self, nota_id: str, categoria: str | None) -> Path:
        carpeta = (self._raiz / categoria) if categoria else self._raiz
        return carpeta / f"{nota_id}.md"

    def _buscar_fichero(self, nota_id: str) -> Path | None:
        # nota_id es único por construcción (Nota.nueva() lo deriva del
        # título, y guardar()/mover() nunca crean dos ficheros con el
        # mismo nombre a la vez), así que basta la primera coincidencia.
        return next(self._raiz.rglob(f"{nota_id}.md"), None)

    def _limpiar_carpetas_vacias(self, carpeta: Path) -> None:
        # Tras mover la última nota de una carpeta, no dejar la
        # carpeta vacía atrás — evita que vault_out/ acumule ramas sin
        # contenido (ver "Crecimiento del árbol" en README.md).
        while carpeta != self._raiz and carpeta.exists() and not any(carpeta.iterdir()):
            carpeta.rmdir()
            carpeta = carpeta.parent

    @staticmethod
    def _a_post(nota: Nota) -> frontmatter.Post:
        return frontmatter.Post(
            nota.contenido,
            titulo=nota.titulo,
            tags=nota.tags,
            categoria=nota.categoria,
            fuente=nota.fuente.value,
            pregunta_origen=nota.pregunta_origen,
            resumen=nota.resumen,
            fecha=nota.creado_en,
        )

    @staticmethod
    def _leer(ruta: Path) -> Nota:
        post = frontmatter.loads(ruta.read_bytes().decode("utf-8"))
        fecha = post.get("fecha")
        if isinstance(fecha, str):
            fecha = date.fromisoformat(fecha)

        return Nota(
            id=ruta.stem,
            titulo=post.get("titulo") or ruta.stem,
            contenido=post.content,
            fuente=FuenteNota(post.get("fuente", FuenteNota.CLI.value)),
            tags=list(post.get("tags") or []),
            categoria=post.get("categoria"),
            pregunta_origen=post.get("pregunta_origen"),
            resumen=post.get("resumen"),
            creado_en=fecha or date.today(),
        )


def _texto_buscable(nota: Nota) -> str:
    return " ".join(filter(None, [nota.titulo, nota.resumen, nota.contenido])).lower()
