"""Excepciones de dominio."""
from __future__ import annotations


class DominioError(Exception):
    """Excepción base de dominio."""


class NotaNoExiste(DominioError):
    """La usan RepositorioNotas.mover() y .eliminar() (ver
    domain/ports.py): a diferencia de obtener(), que devuelve None si
    no existe, estas exigen que la nota ya exista — son operaciones
    sobre algo que se asume presente, no una consulta."""

    def __init__(self, nota_id: str) -> None:
        super().__init__(f"La nota '{nota_id}' no existe.")
        self.nota_id = nota_id


class ExtraccionTextoFallida(DominioError):
    """La lanza ExtractorTexto.extraer (domain/ports.py) cuando el
    fichero no tiene texto extraíble o no es un tipo soportado."""
