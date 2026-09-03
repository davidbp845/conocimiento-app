"""Adaptador de entrada: bot de Telegram, el canal para preguntar
desde cualquier sitio mientras main.py corre en el ordenador (ver
README.md). Usa python-telegram-bot en modo polling — no necesita URL
pública ni webhook, a diferencia del canal de WhatsApp en los
proyectos hermanos."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

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


def crear_aplicacion(
    token: str, responder: ResponderYArchivar, chat_id_permitido: str | None = None
) -> Application:
    app = Application.builder().token(token).build()

    async def _manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat is None or update.message is None or not update.message.text:
            return

        chat_id = str(update.effective_chat.id)
        if chat_id_permitido and chat_id != chat_id_permitido:
            logger.warning("Mensaje ignorado de chat_id no autorizado: %s", chat_id)
            return

        await update.message.reply_text("Buscando la respuesta…")
        respuesta = await procesar_pregunta(update.message.text, responder)
        await update.message.reply_text(respuesta)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _manejar_mensaje))
    return app
