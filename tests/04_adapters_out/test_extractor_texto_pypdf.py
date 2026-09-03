from pathlib import Path

import pytest

from adapters.out.extractor_texto_pypdf import ExtractorTextoPypdf
from domain.exceptions import ExtraccionTextoFallida

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_extrae_texto_de_un_pdf_con_contenido():
    contenido = (_FIXTURES / "documento_ejemplo.pdf").read_bytes()
    texto = ExtractorTextoPypdf().extraer(contenido, "documento_ejemplo.pdf")
    assert "Hola mundo desde un PDF de prueba." in texto


def test_extrae_texto_de_un_txt():
    contenido = (_FIXTURES / "documento_ejemplo.txt").read_bytes()
    texto = ExtractorTextoPypdf().extraer(contenido, "documento_ejemplo.txt")
    assert "Hola mundo desde un fichero de texto de prueba." in texto


def test_pdf_sin_texto_extraible_lanza_extraccion_fallida():
    contenido = (_FIXTURES / "documento_vacio.pdf").read_bytes()
    with pytest.raises(ExtraccionTextoFallida, match="no tiene texto extraíble"):
        ExtractorTextoPypdf().extraer(contenido, "documento_vacio.pdf")


def test_tipo_de_fichero_no_soportado_lanza_extraccion_fallida():
    with pytest.raises(ExtraccionTextoFallida, match="no soportado"):
        ExtractorTextoPypdf().extraer(b"contenido", "imagen.png")


def test_pdf_invalido_lanza_extraccion_fallida():
    with pytest.raises(ExtraccionTextoFallida, match="no es un PDF válido"):
        ExtractorTextoPypdf().extraer(b"esto no es un pdf", "roto.pdf")
