from adapters.out.llm_mock import ClasificadorNotasMock, GeneradorRespuestasMock
from domain.entities import FuenteNota, Nota


def test_generador_mock_no_deja_titulo_vacio_con_pregunta_solo_de_signos():
    respuesta = GeneradorRespuestasMock().generar("???")
    assert respuesta.titulo == "Nota sin título"


def test_generador_mock_incluye_la_pregunta_original_en_el_contenido():
    respuesta = GeneradorRespuestasMock().generar("¿cómo configuro git rebase interactivo?")
    assert "cómo configuro git rebase interactivo" in respuesta.contenido


def test_generador_mock_extrae_palabras_clave_ignorando_vacias_y_cortas():
    respuesta = GeneradorRespuestasMock().generar("¿cómo se configura el rebase en git?")
    assert "rebase" in respuesta.tags_sugeridas
    assert "git" in respuesta.tags_sugeridas
    assert "como" not in respuesta.tags_sugeridas
    assert "el" not in respuesta.tags_sugeridas


def test_resumir_mock_deriva_el_titulo_del_nombre_de_archivo():
    respuesta = GeneradorRespuestasMock().resumir("texto extraído", "informe_anual_2025.pdf")
    assert respuesta.titulo == "Informe anual 2025"


def test_resumir_mock_incluye_el_nombre_de_archivo_en_el_contenido():
    respuesta = GeneradorRespuestasMock().resumir("texto extraído", "notas.md")
    assert "notas.md" in respuesta.contenido


def test_resumir_mock_incluye_la_instruccion_en_el_contenido_si_se_da():
    respuesta = GeneradorRespuestasMock().resumir("texto extraído", "notas.md", "extrae las fechas clave")
    assert "extrae las fechas clave" in respuesta.contenido


def test_clasificador_mock_nunca_propone_categoria():
    nota = Nota.nueva("Título", "contenido", FuenteNota.CLI, tags=["git"])
    sugerencia = ClasificadorNotasMock().clasificar(nota, categorias_existentes=["git", "docker"])
    assert sugerencia.categoria is None
    assert sugerencia.tags == ["git"]
