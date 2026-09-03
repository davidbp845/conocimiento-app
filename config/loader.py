"""Carga config/conocimiento.yaml y la valida contra config/schema.py."""
from __future__ import annotations

import yaml
from pydantic import ValidationError

from config.paths import home
from config.schema import Configuracion


def cargar_config(ruta: str | None = None) -> Configuracion:
    """Devuelve la Configuracion ya validada (no un dict, a diferencia
    del loader de orquestador): aquí no hace falta construir entidades
    de dominio a partir de listas de dicts, así que el propio modelo
    Pydantic ya es cómodo de consumir tal cual (cfg.arbol.umbral...).
    Sin `ruta`, usa config/conocimiento.yaml relativo a home() (ver
    config/paths.py) — no al directorio de trabajo."""
    ruta = ruta or str(home() / "config" / "conocimiento.yaml")
    with open(ruta, encoding="utf-8") as f:
        datos = yaml.safe_load(f) or {}

    try:
        return Configuracion.model_validate(datos)
    except ValidationError as exc:
        raise ValueError(f"Configuración inválida en {ruta}:\n{exc}") from exc
