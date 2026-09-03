import re

import pytest

from config.loader import cargar_config


def test_cargar_config_lee_el_yaml_del_proyecto():
    cfg = cargar_config("config/conocimiento.yaml")
    assert cfg.arbol.umbral_minimo_notas_por_categoria == 5
    assert cfg.arbol.profundidad_maxima_categoria == 2


def test_cargar_config_yaml_vacio_usa_los_defaults_del_schema(tmp_path):
    ruta = tmp_path / "vacio.yaml"
    ruta.write_text("", encoding="utf-8")

    cfg = cargar_config(str(ruta))

    assert cfg.arbol.umbral_minimo_notas_por_categoria == 5
    assert cfg.arbol.profundidad_maxima_categoria == 2


def test_cargar_config_valor_invalido_lanza_value_error_con_la_ruta(tmp_path):
    ruta = tmp_path / "mala.yaml"
    ruta.write_text("arbol:\n  umbral_minimo_notas_por_categoria: -1\n", encoding="utf-8")

    with pytest.raises(ValueError, match=re.escape(str(ruta))):
        cargar_config(str(ruta))
