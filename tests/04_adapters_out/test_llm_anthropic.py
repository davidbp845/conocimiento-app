from unittest.mock import MagicMock, patch

import pytest

from adapters.out.llm_anthropic import (
    ClasificadorNotasAnthropic,
    GeneradorRespuestasAnthropic,
    NormalizadorVaultInAnthropic,
)
from domain.entities import FuenteNota, Nota


class _BloqueToolUseFalso:
    def __init__(self, name: str, input_: dict):
        self.type = "tool_use"
        self.name = name
        self.input = input_


def _cliente_falso(content):
    mensaje = MagicMock()
    mensaje.content = content
    cliente = MagicMock()
    cliente.messages.create.return_value = mensaje
    return cliente


def test_generador_usa_api_key_explicita_en_lugar_de_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        GeneradorRespuestasAnthropic(api_key="explicit-key")
        mock_cls.assert_called_once_with(api_key="explicit-key")


def test_generador_usa_variable_de_entorno_si_no_se_pasa_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        GeneradorRespuestasAnthropic()
        mock_cls.assert_called_once_with(api_key="env-key")


def test_generador_sin_api_key_ni_variable_de_entorno_falla_pronto(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch("adapters.out.llm_anthropic.Anthropic"), pytest.raises(KeyError):
        GeneradorRespuestasAnthropic()


def test_generador_llama_al_sdk_forzando_la_tool_publicar_respuesta(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    entrada = {
        "titulo": "Título", "contenido": "cuerpo", "resumen": "resumen",
        "tags_sugeridas": ["git"],
    }
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        cliente = _cliente_falso([_BloqueToolUseFalso("publicar_respuesta", entrada)])
        mock_cls.return_value = cliente

        respuesta = GeneradorRespuestasAnthropic(modelo="claude-x").generar("¿pregunta?")

        cliente.messages.create.assert_called_once()
        kwargs = cliente.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-x"
        assert kwargs["tool_choice"] == {"type": "tool", "name": "publicar_respuesta"}
        assert kwargs["messages"] == [{"role": "user", "content": "¿pregunta?"}]

    assert respuesta.titulo == "Título"
    assert respuesta.contenido == "cuerpo"
    assert respuesta.tags_sugeridas == ["git"]


def test_resumir_llama_al_sdk_forzando_la_tool_publicar_respuesta(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    entrada = {
        "titulo": "Informe anual", "contenido": "cuerpo", "resumen": "resumen",
        "tags_sugeridas": ["informe"],
    }
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        cliente = _cliente_falso([_BloqueToolUseFalso("publicar_respuesta", entrada)])
        mock_cls.return_value = cliente

        respuesta = GeneradorRespuestasAnthropic(modelo="claude-x").resumir("texto extraído", "informe.pdf")

        cliente.messages.create.assert_called_once()
        kwargs = cliente.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-x"
        assert kwargs["tool_choice"] == {"type": "tool", "name": "publicar_respuesta"}
        assert kwargs["messages"] == [{"role": "user", "content": "Origen: informe.pdf\n\ntexto extraído"}]

    assert respuesta.titulo == "Informe anual"
    assert respuesta.contenido == "cuerpo"
    assert respuesta.tags_sugeridas == ["informe"]


def test_resumir_con_instruccion_la_antepone_al_contenido_del_mensaje(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    entrada = {
        "titulo": "Fechas", "contenido": "cuerpo", "resumen": "resumen",
        "tags_sugeridas": ["informe"],
    }
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        cliente = _cliente_falso([_BloqueToolUseFalso("publicar_respuesta", entrada)])
        mock_cls.return_value = cliente

        GeneradorRespuestasAnthropic(modelo="claude-x").resumir(
            "texto extraído", "informe.pdf", "extrae las fechas clave"
        )

        kwargs = cliente.messages.create.call_args.kwargs
        assert kwargs["messages"] == [{
            "role": "user",
            "content": "Instrucción: extrae las fechas clave\n\nOrigen: informe.pdf\n\ntexto extraído",
        }]


def test_generador_sin_bloque_tool_use_lanza_value_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _cliente_falso([])
        with pytest.raises(ValueError, match="publicar_respuesta"):
            GeneradorRespuestasAnthropic().generar("¿pregunta?")


def test_clasificador_llama_al_sdk_forzando_la_tool_clasificar_nota(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    nota = Nota.nueva("Título", "contenido", FuenteNota.CLI, tags=["git"])
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        cliente = _cliente_falso(
            [_BloqueToolUseFalso("clasificar_nota", {"tags": ["git"], "categoria": "git"})]
        )
        mock_cls.return_value = cliente

        sugerencia = ClasificadorNotasAnthropic().clasificar(nota, ["git", "docker"])

        kwargs = cliente.messages.create.call_args.kwargs
        assert kwargs["tool_choice"] == {"type": "tool", "name": "clasificar_nota"}
        assert "git" in kwargs["system"]
        assert "docker" in kwargs["system"]

    assert sugerencia.categoria == "git"
    assert sugerencia.tags == ["git"]


def test_normalizador_llama_al_sdk_forzando_la_tool_publicar_notas_normalizadas(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    entrada = {
        "notas": [
            {
                "titulo": "Título", "contenido": "cuerpo", "resumen": "resumen",
                "tags": ["git"], "pregunta_origen": None,
            },
        ],
    }
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        cliente = _cliente_falso([_BloqueToolUseFalso("publicar_notas_normalizadas", entrada)])
        mock_cls.return_value = cliente

        normalizadas = NormalizadorVaultInAnthropic(modelo="claude-x").normalizar("texto crudo")

        cliente.messages.create.assert_called_once()
        kwargs = cliente.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-x"
        assert kwargs["tool_choice"] == {"type": "tool", "name": "publicar_notas_normalizadas"}
        assert kwargs["messages"] == [{"role": "user", "content": "texto crudo"}]

    assert len(normalizadas) == 1
    assert normalizadas[0].titulo == "Título"
    assert normalizadas[0].tags == ["git"]
    assert normalizadas[0].pregunta_origen is None


def test_normalizador_puede_devolver_varias_notas(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    entrada = {
        "notas": [
            {"titulo": "Uno", "contenido": "c1", "resumen": "r1", "tags": ["git"], "pregunta_origen": None},
            {"titulo": "Dos", "contenido": "c2", "resumen": "r2", "tags": ["docker"], "pregunta_origen": "¿?"},
        ],
    }
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _cliente_falso(
            [_BloqueToolUseFalso("publicar_notas_normalizadas", entrada)]
        )
        normalizadas = NormalizadorVaultInAnthropic().normalizar("texto con dos temas distintos")

    assert [n.titulo for n in normalizadas] == ["Uno", "Dos"]
    assert normalizadas[1].pregunta_origen == "¿?"


def test_normalizador_sin_bloque_tool_use_lanza_value_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    with patch("adapters.out.llm_anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _cliente_falso([])
        with pytest.raises(ValueError, match="publicar_notas_normalizadas"):
            NormalizadorVaultInAnthropic().normalizar("texto crudo")
