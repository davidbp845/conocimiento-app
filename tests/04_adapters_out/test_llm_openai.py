import json
from unittest.mock import MagicMock, patch

import pytest

from adapters.out.llm_openai import GeneradorRespuestasOpenAI


def _cliente_falso(tool_calls):
    mensaje = MagicMock()
    mensaje.tool_calls = tool_calls
    eleccion = MagicMock()
    eleccion.message = mensaje
    respuesta = MagicMock()
    respuesta.choices = [eleccion]
    cliente = MagicMock()
    cliente.chat.completions.create.return_value = respuesta
    return cliente


def _llamada_falsa(argumentos: dict):
    llamada = MagicMock()
    llamada.function.arguments = json.dumps(argumentos)
    return llamada


def test_generador_usa_api_key_explicita_en_lugar_de_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    with patch("adapters.out.llm_openai.OpenAI") as mock_cls:
        GeneradorRespuestasOpenAI(api_key="explicit-key")
        mock_cls.assert_called_once_with(api_key="explicit-key")


def test_generador_usa_variable_de_entorno_si_no_se_pasa_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    with patch("adapters.out.llm_openai.OpenAI") as mock_cls:
        GeneradorRespuestasOpenAI()
        mock_cls.assert_called_once_with(api_key="env-key")


def test_generador_sin_api_key_ni_variable_de_entorno_falla_pronto(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with patch("adapters.out.llm_openai.OpenAI"), pytest.raises(KeyError):
        GeneradorRespuestasOpenAI()


def test_generador_llama_al_sdk_forzando_la_tool_publicar_respuesta(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    entrada = {
        "titulo": "Título", "contenido": "cuerpo", "resumen": "resumen",
        "tags_sugeridas": ["git"],
    }
    with patch("adapters.out.llm_openai.OpenAI") as mock_cls:
        cliente = _cliente_falso([_llamada_falsa(entrada)])
        mock_cls.return_value = cliente

        respuesta = GeneradorRespuestasOpenAI(modelo="gpt-x").generar("¿pregunta?")

        cliente.chat.completions.create.assert_called_once()
        kwargs = cliente.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "gpt-x"
        assert kwargs["tool_choice"] == {"type": "function", "function": {"name": "publicar_respuesta"}}
        assert kwargs["messages"][-1] == {"role": "user", "content": "¿pregunta?"}

    assert respuesta.titulo == "Título"
    assert respuesta.contenido == "cuerpo"
    assert respuesta.tags_sugeridas == ["git"]


def test_resumir_llama_al_sdk_forzando_la_tool_publicar_respuesta(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    entrada = {
        "titulo": "Informe anual", "contenido": "cuerpo", "resumen": "resumen",
        "tags_sugeridas": ["informe"],
    }
    with patch("adapters.out.llm_openai.OpenAI") as mock_cls:
        cliente = _cliente_falso([_llamada_falsa(entrada)])
        mock_cls.return_value = cliente

        respuesta = GeneradorRespuestasOpenAI(modelo="gpt-x").resumir("texto extraído", "informe.pdf")

        cliente.chat.completions.create.assert_called_once()
        kwargs = cliente.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "gpt-x"
        assert kwargs["tool_choice"] == {"type": "function", "function": {"name": "publicar_respuesta"}}
        assert kwargs["messages"][-1] == {"role": "user", "content": "Origen: informe.pdf\n\ntexto extraído"}

    assert respuesta.titulo == "Informe anual"
    assert respuesta.contenido == "cuerpo"
    assert respuesta.tags_sugeridas == ["informe"]


def test_resumir_con_instruccion_la_antepone_al_contenido_del_mensaje(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    entrada = {
        "titulo": "Fechas", "contenido": "cuerpo", "resumen": "resumen",
        "tags_sugeridas": ["informe"],
    }
    with patch("adapters.out.llm_openai.OpenAI") as mock_cls:
        cliente = _cliente_falso([_llamada_falsa(entrada)])
        mock_cls.return_value = cliente

        GeneradorRespuestasOpenAI(modelo="gpt-x").resumir(
            "texto extraído", "informe.pdf", "extrae las fechas clave"
        )

        kwargs = cliente.chat.completions.create.call_args.kwargs
        assert kwargs["messages"][-1] == {
            "role": "user",
            "content": "Instrucción: extrae las fechas clave\n\nOrigen: informe.pdf\n\ntexto extraído",
        }
