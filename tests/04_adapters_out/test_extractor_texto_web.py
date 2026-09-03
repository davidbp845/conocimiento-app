from unittest.mock import MagicMock, patch

import pytest
import requests

from adapters.out.extractor_texto_web import ExtractorTextoWebHttp
from domain.exceptions import ExtraccionTextoFallida


def _respuesta_falsa(html: str, status_ok: bool = True):
    respuesta = MagicMock()
    respuesta.text = html
    if status_ok:
        respuesta.raise_for_status.return_value = None
    else:
        respuesta.raise_for_status.side_effect = requests.HTTPError("404")
    return respuesta


def test_extrae_texto_visible_descartando_script_y_estilos():
    html = "<html><head><style>body{}</style></head><body><script>alert(1)</script><p>Hola mundo</p></body></html>"
    with patch("adapters.out.extractor_texto_web.requests.get", return_value=_respuesta_falsa(html)):
        texto = ExtractorTextoWebHttp().extraer("https://example.com")

    assert "Hola mundo" in texto
    assert "alert" not in texto


def test_pagina_sin_texto_extraible_lanza_extraccion_fallida():
    html = "<html><body><script>alert(1)</script></body></html>"
    with patch("adapters.out.extractor_texto_web.requests.get", return_value=_respuesta_falsa(html)):
        with pytest.raises(ExtraccionTextoFallida, match="no tiene texto extraíble"):
            ExtractorTextoWebHttp().extraer("https://example.com")


def test_error_de_red_lanza_extraccion_fallida():
    with patch("adapters.out.extractor_texto_web.requests.get", side_effect=requests.ConnectionError("caída")):
        with pytest.raises(ExtraccionTextoFallida, match="No he podido descargar"):
            ExtractorTextoWebHttp().extraer("https://example.com")


def test_estado_http_de_error_lanza_extraccion_fallida():
    with patch(
        "adapters.out.extractor_texto_web.requests.get",
        return_value=_respuesta_falsa("<html></html>", status_ok=False),
    ):
        with pytest.raises(ExtraccionTextoFallida, match="No he podido descargar"):
            ExtractorTextoWebHttp().extraer("https://example.com/404")
