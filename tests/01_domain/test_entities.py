from datetime import date

from domain.entities import FuenteNota, Movimiento, Nota, RespuestaGenerada, SugerenciaClasificacion, slug


def test_slug_minusculas_sin_acentos_y_con_guiones():
    assert slug("¿Cómo revertir el último commit?") == "como-revertir-el-ultimo-commit"


def test_slug_recorta_a_la_longitud_maxima_sin_guion_colgante():
    resultado = slug("a" * 5 + "-" + "b" * 60, longitud_maxima=10)
    assert len(resultado) <= 10
    assert not resultado.endswith("-")


def test_slug_de_texto_vacio_devuelve_fallback():
    assert slug("   ") == "nota"


def test_nota_nueva_deriva_el_id_del_titulo():
    nota = Nota.nueva("Cómo usar git rebase", "contenido", FuenteNota.CLI)
    assert nota.id == "como-usar-git-rebase"
    assert nota.categoria is None
    assert nota.tags == []
    assert nota.creado_en == date.today()


def test_nota_nueva_con_tags_y_metadatos_opcionales():
    nota = Nota.nueva(
        "Título", "contenido", FuenteNota.TELEGRAM,
        tags=["git", "cli"], pregunta_origen="¿pregunta?", resumen="resumen",
    )
    assert nota.tags == ["git", "cli"]
    assert nota.pregunta_origen == "¿pregunta?"
    assert nota.resumen == "resumen"
    assert nota.fuente == FuenteNota.TELEGRAM


def test_fuente_nota_incluye_manual_para_md_pegados_a_mano():
    assert FuenteNota.MANUAL == "manual"


def test_respuesta_generada_valores_por_defecto():
    respuesta = RespuestaGenerada(titulo="t", contenido="c")
    assert respuesta.resumen is None
    assert respuesta.tags_sugeridas == []


def test_sugerencia_clasificacion_categoria_none_significa_seguir_en_la_raiz():
    sugerencia = SugerenciaClasificacion(tags=["git"], categoria=None)
    assert sugerencia.categoria is None


def test_movimiento_guarda_origen_y_destino():
    movimiento = Movimiento(nota_id="n1", categoria_actual=None, categoria_propuesta="git")
    assert movimiento.categoria_actual is None
    assert movimiento.categoria_propuesta == "git"
