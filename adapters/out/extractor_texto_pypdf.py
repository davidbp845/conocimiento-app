"""Implementación de ExtractorTexto: PDFs vía pypdf, texto plano (.txt,
.md) por decodificación directa. Es lo único que sabe de pypdf en todo
el proyecto — domain/ solo conoce el puerto ExtractorTexto."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from domain.exceptions import ExtraccionTextoFallida
from domain.ports import ExtractorTexto


class ExtractorTextoPypdf(ExtractorTexto):
    def extraer(self, contenido: bytes, nombre_archivo: str) -> str:
        extension = Path(nombre_archivo).suffix.lower()
        if extension == ".pdf":
            texto = self._extraer_pdf(contenido, nombre_archivo)
        elif extension in (".txt", ".md"):
            texto = contenido.decode("utf-8", errors="replace")
        else:
            raise ExtraccionTextoFallida(f"Tipo de fichero no soportado: '{extension or nombre_archivo}'.")

        if not texto.strip():
            raise ExtraccionTextoFallida(
                f"'{nombre_archivo}' no tiene texto extraíble (¿un PDF escaneado sin OCR?)."
            )
        return texto

    def _extraer_pdf(self, contenido: bytes, nombre_archivo: str) -> str:
        try:
            lector = PdfReader(BytesIO(contenido))
        except PdfReadError as e:
            raise ExtraccionTextoFallida(f"'{nombre_archivo}' no es un PDF válido: {e}") from e
        return "\n\n".join(pagina.extract_text() or "" for pagina in lector.pages)
