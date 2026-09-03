from telegram.ext import Application

from adapters.in_.telegram_bot import crear_aplicacion, procesar_pregunta
from domain.entities import FuenteNota, Nota


class ResponderFake:
    def __init__(self, nota=None, excepcion=None):
        self._nota = nota
        self._excepcion = excepcion
        self.llamadas: list[tuple[str, FuenteNota]] = []

    def ejecutar(self, pregunta: str, fuente: FuenteNota) -> Nota:
        self.llamadas.append((pregunta, fuente))
        if self._excepcion:
            raise self._excepcion
        return self._nota


async def test_procesar_pregunta_devuelve_el_contenido_y_el_id_de_la_nota():
    nota = Nota.nueva("Título", "contenido de la respuesta", FuenteNota.TELEGRAM)
    responder = ResponderFake(nota=nota)

    resultado = await procesar_pregunta("¿pregunta?", responder)

    assert "contenido de la respuesta" in resultado
    assert nota.id in resultado
    assert responder.llamadas == [("¿pregunta?", FuenteNota.TELEGRAM)]


async def test_procesar_pregunta_con_fallo_no_propaga_la_excepcion():
    responder = ResponderFake(excepcion=RuntimeError("boom"))

    resultado = await procesar_pregunta("¿pregunta?", responder)

    assert "No he podido generar la respuesta" in resultado


def test_crear_aplicacion_registra_un_manejador_de_mensajes():
    app = crear_aplicacion("token-falso", ResponderFake())

    assert isinstance(app, Application)
    assert len(app.handlers[0]) == 1
