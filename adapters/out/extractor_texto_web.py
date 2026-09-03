"""Implementación de ExtractorTextoWeb: descarga la URL con requests y
extrae el texto visible con BeautifulSoup, descartando script/estilos/
navegación. Es lo único que sabe de requests/bs4 en todo el proyecto —
domain/ solo conoce el puerto ExtractorTextoWeb."""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from domain.exceptions import ExtraccionTextoFallida
from domain.ports import ExtractorTextoWeb

_TIMEOUT_SEGUNDOS = 15
_USER_AGENT = "Mozilla/5.0 (compatible; conocimiento-bot/1.0)"
# Descartadas por no ser contenido legible de la página (código,
# maquetación, navegación) — no por relevancia semántica, así que no
# hace falta más finura que esta lista fija.
_ETIQUETAS_A_DESCARTAR = ("script", "style", "noscript", "nav", "footer", "header")


class ExtractorTextoWebHttp(ExtractorTextoWeb):
    def extraer(self, url: str) -> str:
        try:
            respuesta = requests.get(url, timeout=_TIMEOUT_SEGUNDOS, headers={"User-Agent": _USER_AGENT})
            respuesta.raise_for_status()
        except requests.RequestException as e:
            raise ExtraccionTextoFallida(f"No he podido descargar '{url}': {e}") from e

        sopa = BeautifulSoup(respuesta.text, "html.parser")
        for etiqueta in sopa(_ETIQUETAS_A_DESCARTAR):
            etiqueta.decompose()

        texto = sopa.get_text("\n", strip=True)
        if not texto:
            raise ExtraccionTextoFallida(f"'{url}' no tiene texto extraíble.")
        return texto
