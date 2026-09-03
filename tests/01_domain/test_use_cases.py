import pytest

from domain.entities import FuenteNota, Movimiento, Nota, RespuestaGenerada, SugerenciaClasificacion
from domain.exceptions import ExtraccionTextoFallida, NotaNoExiste
from domain.ports import ClasificadorNotas, ExtractorTexto, ExtractorTextoWeb, GeneradorRespuestas, RepositorioNotas
from domain.use_cases import (
    PROFUNDIDAD_MAXIMA_CATEGORIA,
    UMBRAL_MINIMO_NOTAS_POR_CATEGORIA,
    AplicarReorganizacion,
    ArchivarNotaRedactada,
    BuscarNotas,
    EliminarNota,
    PlanificarReorganizacion,
    ResponderYArchivar,
    ResumirYArchivarDocumento,
    ResumirYArchivarPaginaWeb,
)


class RepositorioNotasFake(RepositorioNotas):
    def __init__(self):
        self._notas: dict[str, Nota] = {}

    def guardar(self, nota: Nota) -> None:
        self._notas[nota.id] = nota

    def obtener(self, nota_id: str) -> Nota | None:
        return self._notas.get(nota_id)

    def listar(self) -> list[Nota]:
        return list(self._notas.values())

    def buscar(self, texto: str | None = None, tags: list[str] | None = None) -> list[Nota]:
        notas = list(self._notas.values())
        if texto:
            notas = [n for n in notas if texto.lower() in (n.titulo + n.contenido).lower()]
        if tags:
            notas = [n for n in notas if set(tags) <= set(n.tags)]
        return notas

    def listar_categorias(self) -> list[str]:
        return sorted({n.categoria for n in self._notas.values() if n.categoria})

    def mover(self, nota_id: str, nueva_categoria: str | None) -> None:
        if nota_id not in self._notas:
            raise NotaNoExiste(nota_id)
        self._notas[nota_id].categoria = nueva_categoria

    def eliminar(self, nota_id: str) -> None:
        if nota_id not in self._notas:
            raise NotaNoExiste(nota_id)
        del self._notas[nota_id]


class GeneradorRespuestasFake(GeneradorRespuestas):
    def __init__(self, respuesta: RespuestaGenerada):
        self._respuesta = respuesta

    def generar(self, pregunta: str) -> RespuestaGenerada:
        return self._respuesta

    def resumir(self, texto: str, nombre_archivo: str, instruccion: str | None = None) -> RespuestaGenerada:
        return self._respuesta


class ExtractorTextoFake(ExtractorTexto):
    """texto se devuelve tal cual; error (si se da) se lanza en vez de
    devolver nada — suficiente para ejercitar tanto el camino feliz como
    la propagación de ExtraccionTextoFallida sin necesitar pypdf."""

    def __init__(self, texto: str = "", error: Exception | None = None):
        self._texto = texto
        self._error = error

    def extraer(self, contenido: bytes, nombre_archivo: str) -> str:
        if self._error is not None:
            raise self._error
        return self._texto


class ExtractorTextoWebFake(ExtractorTextoWeb):
    """Igual que ExtractorTextoFake pero para el puerto ExtractorTextoWeb
    (una URL en vez de bytes + nombre de fichero)."""

    def __init__(self, texto: str = "", error: Exception | None = None):
        self._texto = texto
        self._error = error

    def extraer(self, url: str) -> str:
        if self._error is not None:
            raise self._error
        return self._texto


class ClasificadorNotasFake(ClasificadorNotas):
    """Clasifica todo bajo 'git' salvo que el título contenga 'suelta',
    que deja sin categoria — suficiente para ejercitar ambas ramas de
    PlanificarReorganizacion sin necesitar un LLM de verdad."""

    def clasificar(self, nota: Nota, categorias_existentes: list[str]) -> SugerenciaClasificacion:
        if "suelta" in nota.titulo:
            return SugerenciaClasificacion(tags=nota.tags, categoria=None)
        return SugerenciaClasificacion(tags=nota.tags, categoria="git")


class ClasificadorProfundidadExcesivaFake(ClasificadorNotas):
    def clasificar(self, nota: Nota, categorias_existentes: list[str]) -> SugerenciaClasificacion:
        return SugerenciaClasificacion(tags=nota.tags, categoria="a/b/c")


def test_responder_y_archivar_guarda_nota_plana_con_los_datos_del_generador():
    repo = RepositorioNotasFake()
    respuesta = RespuestaGenerada(
        titulo="Cómo hacer X", contenido="cuerpo", resumen="resumen", tags_sugeridas=["git"],
    )
    uc = ResponderYArchivar(GeneradorRespuestasFake(respuesta), repo)

    nota = uc.ejecutar("¿cómo hago X?", FuenteNota.TELEGRAM)

    assert nota.id == "como-hacer-x"
    assert nota.categoria is None
    assert nota.fuente == FuenteNota.TELEGRAM
    assert nota.pregunta_origen == "¿cómo hago X?"
    assert repo.obtener("como-hacer-x") == nota


def test_archivar_nota_redactada_usa_siempre_fuente_claude_code():
    repo = RepositorioNotasFake()
    nota = ArchivarNotaRedactada(repo).ejecutar(titulo="Título", contenido="cuerpo")
    assert nota.fuente == FuenteNota.CLAUDE_CODE
    assert repo.obtener(nota.id) is not None


def test_resumir_y_archivar_documento_guarda_nota_plana_con_los_datos_del_generador():
    repo = RepositorioNotasFake()
    respuesta = RespuestaGenerada(
        titulo="Informe anual", contenido="cuerpo", resumen="resumen", tags_sugeridas=["informe"],
    )
    uc = ResumirYArchivarDocumento(
        ExtractorTextoFake(texto="texto extraído"), GeneradorRespuestasFake(respuesta), repo
    )

    nota = uc.ejecutar(b"bytes", "informe.pdf", FuenteNota.STREAMLIT)

    assert nota.id == "informe-anual"
    assert nota.categoria is None
    assert nota.fuente == FuenteNota.STREAMLIT
    assert nota.pregunta_origen == "Resumen del documento «informe.pdf»"
    assert repo.obtener("informe-anual") == nota


def test_resumir_y_archivar_documento_con_instruccion_la_pasa_al_generador_y_a_pregunta_origen():
    repo = RepositorioNotasFake()
    respuesta = RespuestaGenerada(
        titulo="Fechas del informe", contenido="cuerpo", resumen="resumen", tags_sugeridas=["informe"],
    )

    class GeneradorRespuestasEspia(GeneradorRespuestas):
        instruccion_recibida: str | None = None

        def generar(self, pregunta: str) -> RespuestaGenerada:
            return respuesta

        def resumir(self, texto: str, nombre_archivo: str, instruccion: str | None = None) -> RespuestaGenerada:
            GeneradorRespuestasEspia.instruccion_recibida = instruccion
            return respuesta

    uc = ResumirYArchivarDocumento(ExtractorTextoFake(texto="texto extraído"), GeneradorRespuestasEspia(), repo)

    nota = uc.ejecutar(b"bytes", "informe.pdf", FuenteNota.STREAMLIT, instruccion="extrae las fechas clave")

    assert GeneradorRespuestasEspia.instruccion_recibida == "extrae las fechas clave"
    assert nota.pregunta_origen == "extrae las fechas clave (documento «informe.pdf»)"


def test_resumir_y_archivar_documento_propaga_extraccion_texto_fallida_sin_guardar_nada():
    repo = RepositorioNotasFake()
    extractor = ExtractorTextoFake(error=ExtraccionTextoFallida("no hay texto"))
    respuesta = RespuestaGenerada(titulo="t", contenido="c")
    uc = ResumirYArchivarDocumento(extractor, GeneradorRespuestasFake(respuesta), repo)

    with pytest.raises(ExtraccionTextoFallida):
        uc.ejecutar(b"bytes", "escaneado.pdf", FuenteNota.STREAMLIT)

    assert repo.listar() == []


def test_resumir_y_archivar_pagina_web_guarda_nota_plana_con_los_datos_del_generador():
    repo = RepositorioNotasFake()
    respuesta = RespuestaGenerada(
        titulo="Artículo interesante", contenido="cuerpo", resumen="resumen", tags_sugeridas=["web"],
    )
    uc = ResumirYArchivarPaginaWeb(
        ExtractorTextoWebFake(texto="texto extraído"), GeneradorRespuestasFake(respuesta), repo
    )

    nota = uc.ejecutar("https://example.com/articulo", FuenteNota.STREAMLIT)

    assert nota.id == "articulo-interesante"
    assert nota.categoria is None
    assert nota.fuente == FuenteNota.STREAMLIT
    assert nota.pregunta_origen == "Resumen de la página «https://example.com/articulo»"
    assert repo.obtener("articulo-interesante") == nota


def test_resumir_y_archivar_pagina_web_con_instruccion_la_pasa_al_generador_y_a_pregunta_origen():
    repo = RepositorioNotasFake()
    respuesta = RespuestaGenerada(
        titulo="Fechas del artículo", contenido="cuerpo", resumen="resumen", tags_sugeridas=["web"],
    )

    class GeneradorRespuestasEspia(GeneradorRespuestas):
        instruccion_recibida: str | None = None

        def generar(self, pregunta: str) -> RespuestaGenerada:
            return respuesta

        def resumir(self, texto: str, nombre_archivo: str, instruccion: str | None = None) -> RespuestaGenerada:
            GeneradorRespuestasEspia.instruccion_recibida = instruccion
            return respuesta

    uc = ResumirYArchivarPaginaWeb(
        ExtractorTextoWebFake(texto="texto extraído"), GeneradorRespuestasEspia(), repo
    )

    nota = uc.ejecutar(
        "https://example.com/articulo", FuenteNota.STREAMLIT, instruccion="extrae las fechas clave"
    )

    assert GeneradorRespuestasEspia.instruccion_recibida == "extrae las fechas clave"
    assert nota.pregunta_origen == "extrae las fechas clave (página «https://example.com/articulo»)"


def test_resumir_y_archivar_pagina_web_propaga_extraccion_texto_fallida_sin_guardar_nada():
    repo = RepositorioNotasFake()
    extractor = ExtractorTextoWebFake(error=ExtraccionTextoFallida("no alcanzable"))
    respuesta = RespuestaGenerada(titulo="t", contenido="c")
    uc = ResumirYArchivarPaginaWeb(extractor, GeneradorRespuestasFake(respuesta), repo)

    with pytest.raises(ExtraccionTextoFallida):
        uc.ejecutar("https://example.com/caida", FuenteNota.STREAMLIT)

    assert repo.listar() == []


def test_buscar_notas_delega_en_el_repositorio():
    repo = RepositorioNotasFake()
    repo.guardar(Nota.nueva("Sobre git", "contenido con git", FuenteNota.CLI, tags=["git"]))
    repo.guardar(Nota.nueva("Sobre docker", "contenido con docker", FuenteNota.CLI, tags=["docker"]))

    resultado = BuscarNotas(repo).ejecutar(tags=["git"])

    assert [n.id for n in resultado] == ["sobre-git"]


def test_eliminar_nota_delega_en_el_repositorio():
    repo = RepositorioNotasFake()
    repo.guardar(Nota.nueva("Sobre git", "contenido", FuenteNota.CLI))

    EliminarNota(repo).ejecutar("sobre-git")

    assert repo.obtener("sobre-git") is None


def test_eliminar_nota_inexistente_propaga_nota_no_existe():
    repo = RepositorioNotasFake()

    with pytest.raises(NotaNoExiste):
        EliminarNota(repo).ejecutar("no-existe")


def test_planificar_reorganizacion_no_crea_categoria_nueva_bajo_el_umbral():
    repo = RepositorioNotasFake()
    for i in range(UMBRAL_MINIMO_NOTAS_POR_CATEGORIA - 1):
        repo.guardar(Nota.nueva(f"Nota git {i}", "c", FuenteNota.CLI))

    plan = PlanificarReorganizacion(repo, ClasificadorNotasFake()).ejecutar()

    assert plan == []


def test_planificar_reorganizacion_crea_categoria_nueva_al_alcanzar_el_umbral():
    repo = RepositorioNotasFake()
    for i in range(UMBRAL_MINIMO_NOTAS_POR_CATEGORIA):
        repo.guardar(Nota.nueva(f"Nota git {i}", "c", FuenteNota.CLI))

    plan = PlanificarReorganizacion(repo, ClasificadorNotasFake()).ejecutar()

    assert len(plan) == UMBRAL_MINIMO_NOTAS_POR_CATEGORIA
    assert all(m.categoria_propuesta == "git" for m in plan)


def test_planificar_reorganizacion_ignora_notas_que_el_clasificador_deja_sin_categoria():
    repo = RepositorioNotasFake()
    repo.guardar(Nota.nueva("Nota suelta", "c", FuenteNota.CLI))

    plan = PlanificarReorganizacion(repo, ClasificadorNotasFake()).ejecutar()

    assert plan == []


def test_planificar_reorganizacion_reusa_categoria_existente_sin_necesitar_umbral():
    repo = RepositorioNotasFake()
    repo.guardar(Nota.nueva("Ya clasificada", "c", FuenteNota.CLI))
    repo.mover("ya-clasificada", "git")
    repo.guardar(Nota.nueva("Nota nueva", "c", FuenteNota.CLI))

    plan = PlanificarReorganizacion(repo, ClasificadorNotasFake()).ejecutar()

    assert plan == [Movimiento(nota_id="nota-nueva", categoria_actual=None, categoria_propuesta="git")]


def test_planificar_reorganizacion_respeta_la_profundidad_maxima():
    repo = RepositorioNotasFake()
    for i in range(UMBRAL_MINIMO_NOTAS_POR_CATEGORIA):
        repo.guardar(Nota.nueva(f"Nota profunda {i}", "c", FuenteNota.CLI))

    plan = PlanificarReorganizacion(repo, ClasificadorProfundidadExcesivaFake()).ejecutar()

    assert plan == []
    assert PROFUNDIDAD_MAXIMA_CATEGORIA == 2  # documenta el supuesto del test


def test_aplicar_reorganizacion_mueve_cada_nota_del_plan():
    repo = RepositorioNotasFake()
    for i in range(UMBRAL_MINIMO_NOTAS_POR_CATEGORIA):
        repo.guardar(Nota.nueva(f"Nota git {i}", "c", FuenteNota.CLI))

    plan = PlanificarReorganizacion(repo, ClasificadorNotasFake()).ejecutar()
    AplicarReorganizacion(repo).ejecutar(plan)

    assert all(n.categoria == "git" for n in repo.listar())


def test_aplicar_reorganizacion_propaga_nota_no_existe():
    repo = RepositorioNotasFake()
    plan = [Movimiento(nota_id="no-existe", categoria_actual=None, categoria_propuesta="git")]

    with pytest.raises(NotaNoExiste):
        AplicarReorganizacion(repo).ejecutar(plan)
