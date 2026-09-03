import pytest
from pydantic import ValidationError

from config.schema import Configuracion, ConfiguracionArbol


def test_configuracion_arbol_valores_por_defecto():
    arbol = ConfiguracionArbol()
    assert arbol.umbral_minimo_notas_por_categoria == 5
    assert arbol.profundidad_maxima_categoria == 2


def test_configuracion_arbol_rechaza_valores_no_positivos():
    with pytest.raises(ValidationError):
        ConfiguracionArbol(umbral_minimo_notas_por_categoria=0)


def test_configuracion_sin_bloque_arbol_usa_el_default_factory():
    cfg = Configuracion.model_validate({})
    assert cfg.arbol.umbral_minimo_notas_por_categoria == 5
