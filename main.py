"""Composition root: conecta dominio y adaptadores, y arranca el bot
de Telegram — el "proceso funcionando en el ordenador" del README.md.
Sin TELEGRAM_BOT_TOKEN no hay nada que arrancar aquí; mientras tanto,
usa `python -m adapters.in_.cli` (ver también .claude/commands/)."""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from adapters.in_.telegram_bot import crear_aplicacion
from adapters.out.repositorio_notas_filesystem import RepositorioNotasFilesystem
from config.paths import home
from domain.use_cases import ResponderYArchivar

load_dotenv(home() / ".env")

logger = logging.getLogger(__name__)


def construir_generador():
    if os.environ.get("PROVEEDOR_LLM", "anthropic") == "mock":
        from adapters.out.llm_mock import GeneradorRespuestasMock
        return GeneradorRespuestasMock()
    from adapters.out.llm_anthropic import GeneradorRespuestasAnthropic
    return GeneradorRespuestasAnthropic()


def construir_sistema() -> ResponderYArchivar:
    notas = RepositorioNotasFilesystem(os.environ.get("VAULT_OUT_PATH", str(home() / "vault_out")))
    return ResponderYArchivar(construir_generador(), notas)


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN no está configurado (ver .env.example). "
            "Sin él no hay nada que arrancar en main.py — usa "
            "`python -m adapters.in_.cli` mientras tanto."
        )

    app = crear_aplicacion(
        token,
        construir_sistema(),
        chat_id_permitido=os.environ.get("TELEGRAM_CHAT_ID_PERMITIDO"),
    )
    logger.info("Bot de Telegram arrancado (polling).")
    app.run_polling()


if __name__ == "__main__":
    main()
