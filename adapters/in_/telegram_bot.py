"""Adaptador de entrada: bot de Telegram, el canal para preguntar
desde cualquier sitio mientras main.py corre en el ordenador (ver
README.md). Usa python-telegram-bot en modo polling — no necesita URL
pública ni webhook, a diferencia del canal de WhatsApp en los
proyectos hermanos."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from domain.entities import FuenteNota
from domain.use_cases import ResponderYArchivar

logger = logging.getLogger(__name__)


async def procesar_pregunta(pregunta: str, responder: ResponderYArchivar) -> str:
    """Parte sin dependencias de Telegram del manejador de mensajes —
    separada para poder probarla con un ResponderYArchivar de mentira,
    sin construir un Update real del SDK."""
    try:
        nota = responder.ejecutar(pregunta, FuenteNota.TELEGRAM)
    except Exception:
        logger.exception("Fallo generando/guardando la respuesta a: %s", pregunta)
        return "No he podido generar la respuesta, inténtalo de nuevo."
    return f"{nota.contenido}\n\n(guardada como {nota.id})"


class GestorConversaciones:
    """Acumula en memoria los mensajes de texto de una conversación de
    Telegram entre /iniciar y /finalizar, por chat — para volcarlos en
    bloque a vault_in/ al cerrarla (ver guardar_conversacion). Solo en
    memoria a propósito: si el proceso se reinicia a media captura, se
    pierde en vez de volcarse a medias a vault_in/ sin que nadie lo
    haya pedido con /finalizar."""

    def __init__(self) -> None:
        self._en_curso: dict[str, list[str]] = {}

    def en_curso(self, chat_id: str) -> bool:
        return chat_id in self._en_curso

    def iniciar(self, chat_id: str) -> bool:
        """True si arranca una conversación nueva; False si ya había
        una en curso para ese chat (no la reinicia ni la pierde)."""
        if chat_id in self._en_curso:
            return False
        self._en_curso[chat_id] = []
        return True

    def anadir(self, chat_id: str, texto: str) -> None:
        self._en_curso[chat_id].append(texto)

    def finalizar(self, chat_id: str) -> list[str] | None:
        """Devuelve los mensajes acumulados y cierra la conversación
        (None si no había ninguna en curso)."""
        return self._en_curso.pop(chat_id, None)


def guardar_conversacion(mensajes: list[str], vault_in: Path) -> str:
    """Vuelca los mensajes de una conversación ya cerrada como un único
    .md en vault_in/, sin frontmatter (igual que cualquier fichero
    pegado a mano ahí — ver vault_in/README.md), uno por párrafo y en
    el mismo orden en que se escribieron. Devuelve el nombre del
    fichero creado."""
    vault_in.mkdir(parents=True, exist_ok=True)
    # Microsegundos incluidos: dos /finalizar seguidos (chats distintos,
    # o el mismo muy rápido) no deben poder colisionar en el mismo nombre
    # y pisarse el uno al otro.
    nombre = f"telegram-{datetime.now():%Y-%m-%d-%H%M%S-%f}.md"
    (vault_in / nombre).write_text("\n\n".join(mensajes) + "\n", encoding="utf-8")
    return nombre


def crear_aplicacion(
    token: str,
    responder: ResponderYArchivar,
    vault_in: Path | str,
    chat_id_permitido: str | None = None,
) -> Application:
    app = Application.builder().token(token).build()
    vault_in = Path(vault_in)
    conversaciones = GestorConversaciones()

    def _chat_autorizado(update: Update) -> str | None:
        if update.effective_chat is None:
            return None
        chat_id = str(update.effective_chat.id)
        if chat_id_permitido and chat_id != chat_id_permitido:
            logger.warning("Mensaje ignorado de chat_id no autorizado: %s", chat_id)
            return None
        return chat_id

    async def _iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = _chat_autorizado(update)
        if chat_id is None or update.message is None:
            return
        if not conversaciones.iniciar(chat_id):
            await update.message.reply_text(
                "Ya había una conversación en curso — sigue escribiendo o manda /finalizar."
            )
            return
        await update.message.reply_text(
            "Conversación iniciada: todo lo que escribas a partir de ahora se guarda tal "
            "cual (sin responder) hasta que mandes /finalizar."
        )

    async def _finalizar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = _chat_autorizado(update)
        if chat_id is None or update.message is None:
            return
        mensajes = conversaciones.finalizar(chat_id)
        if not mensajes:
            await update.message.reply_text("No había ninguna conversación en curso (usa /iniciar antes).")
            return
        nombre = guardar_conversacion(mensajes, vault_in)
        await update.message.reply_text(
            f"Guardada en vault_in/{nombre} ({len(mensajes)} mensaje(s)) — pendiente de /normalizar-vault-in."
        )

    async def _manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat is None or update.message is None or not update.message.text:
            return

        chat_id = _chat_autorizado(update)
        if chat_id is None:
            return

        if conversaciones.en_curso(chat_id):
            conversaciones.anadir(chat_id, update.message.text)
            await update.message.reply_text("✓")
            return

        await update.message.reply_text("Buscando la respuesta…")
        respuesta = await procesar_pregunta(update.message.text, responder)
        await update.message.reply_text(respuesta)

    app.add_handler(CommandHandler("iniciar", _iniciar))
    app.add_handler(CommandHandler("finalizar", _finalizar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _manejar_mensaje))
    return app
