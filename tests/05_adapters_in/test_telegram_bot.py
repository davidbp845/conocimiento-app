from telegram.ext import Application

from adapters.in_.telegram_bot import (
    GestorConversaciones,
    crear_aplicacion,
    guardar_conversacion,
    procesar_pregunta,
)
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


def test_crear_aplicacion_registra_los_manejadores(tmp_path):
    app = crear_aplicacion("token-falso", ResponderFake(), vault_in=tmp_path)

    assert isinstance(app, Application)
    # /iniciar, /finalizar y el manejador de mensajes de texto.
    assert len(app.handlers[0]) == 3


class TestGestorConversaciones:
    def test_iniciar_arranca_una_conversacion_vacia(self):
        gestor = GestorConversaciones()

        assert gestor.iniciar("chat-1") is True
        assert gestor.en_curso("chat-1") is True
        assert gestor.finalizar("chat-1") == []

    def test_iniciar_dos_veces_no_pierde_lo_ya_acumulado(self):
        gestor = GestorConversaciones()
        gestor.iniciar("chat-1")
        gestor.anadir("chat-1", "primer mensaje")

        assert gestor.iniciar("chat-1") is False
        assert gestor.finalizar("chat-1") == ["primer mensaje"]

    def test_anadir_acumula_en_orden(self):
        gestor = GestorConversaciones()
        gestor.iniciar("chat-1")
        gestor.anadir("chat-1", "uno")
        gestor.anadir("chat-1", "dos")

        assert gestor.finalizar("chat-1") == ["uno", "dos"]

    def test_finalizar_sin_conversacion_en_curso_devuelve_none(self):
        gestor = GestorConversaciones()

        assert gestor.finalizar("chat-1") is None

    def test_finalizar_cierra_la_conversacion(self):
        gestor = GestorConversaciones()
        gestor.iniciar("chat-1")

        gestor.finalizar("chat-1")

        assert gestor.en_curso("chat-1") is False

    def test_conversaciones_de_chats_distintos_no_se_mezclan(self):
        gestor = GestorConversaciones()
        gestor.iniciar("chat-1")
        gestor.iniciar("chat-2")
        gestor.anadir("chat-1", "de chat 1")
        gestor.anadir("chat-2", "de chat 2")

        assert gestor.finalizar("chat-1") == ["de chat 1"]
        assert gestor.finalizar("chat-2") == ["de chat 2"]


class TestGuardarConversacion:
    def test_escribe_un_fichero_con_los_mensajes_separados_por_parrafo(self, tmp_path):
        nombre = guardar_conversacion(["primero", "segundo"], tmp_path)

        contenido = (tmp_path / nombre).read_text(encoding="utf-8")
        assert contenido == "primero\n\nsegundo\n"

    def test_devuelve_un_nombre_distinto_para_cada_llamada(self, tmp_path):
        nombre_1 = guardar_conversacion(["a"], tmp_path)
        nombre_2 = guardar_conversacion(["b"], tmp_path)

        assert nombre_1 != nombre_2

    def test_crea_vault_in_si_no_existe(self, tmp_path):
        vault_in = tmp_path / "no-existe-todavia"

        guardar_conversacion(["mensaje"], vault_in)

        assert vault_in.is_dir()
