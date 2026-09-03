"""Schema de validación de config/conocimiento.yaml. Sin esto, un typo
o un valor fuera de rango en el YAML solo se descubriría cuando
PlanificarReorganizacion lo intentara usar, a mitad de un
`reorganizar --aplicar`. cargar_config() valida contra este schema al
cargarlo, así que el fallo (si lo hay) es inmediato y señala
exactamente qué campo está mal.

No importa nada de domain/ a propósito: config/ es una capa externa
que describe cómo arrancar el sistema, no depende de sus tipos. Es
`config/loader.py` (o main.py) quien traduce esta config validada a lo
que domain/use_cases.py espera."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ConfiguracionArbol(BaseModel):
    """Límites que debe respetar PlanificarReorganizacion (ver
    domain/use_cases.py) al proponer subcarpetas nuevas para
    vault_out/. Los valores por defecto son los mismos que documenta
    "Crecimiento del árbol" en README.md."""

    umbral_minimo_notas_por_categoria: int = Field(default=5, gt=0)
    profundidad_maxima_categoria: int = Field(default=2, gt=0)


class Configuracion(BaseModel):
    arbol: ConfiguracionArbol = Field(default_factory=ConfiguracionArbol)
