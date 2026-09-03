import io

import pytest

from adapters.in_.cli import main
from adapters.out.repositorio_notas_filesystem import RepositorioNotasFilesystem
from domain.entities import FuenteNota, Nota


@pytest.fixture(autouse=True)
def entorno(tmp_path, monkeypatch):
    vault = tmp_path / "vault_out"
    vault.mkdir()
    monkeypatch.setenv("VAULT_OUT_PATH", str(vault))
    # mock: ni CLI ni tests dependen de red ni de ANTHROPIC_API_KEY.
    monkeypatch.setenv("PROVEEDOR_LLM", "mock")
    return vault


def test_guardar_desde_archivo_respeta_el_frontmatter_propio(tmp_path, entorno, capsys):
    origen = tmp_path / "borrador.md"
    origen.write_text(
        "---\ntitulo: Mi título\ntags: [git]\n---\n# Cuerpo\ncontenido\n",
        encoding="utf-8",
    )

    main(["guardar", "--archivo", str(origen)])

    assert "mi-titulo.md" in capsys.readouterr().out
    assert (entorno / "mi-titulo.md").exists()


def test_guardar_desde_archivo_sin_frontmatter_usa_la_primera_linea_como_titulo(tmp_path, entorno):
    origen = tmp_path / "borrador.md"
    origen.write_text("# Cómo hacer algo\ncontenido\n", encoding="utf-8")

    main(["guardar", "--archivo", str(origen)])

    assert (entorno / "como-hacer-algo.md").exists()


def test_guardar_desde_stdin(monkeypatch, entorno):
    monkeypatch.setattr("sys.stdin", io.StringIO("# Desde stdin\ncontenido\n"))

    main(["guardar", "--stdin"])

    assert (entorno / "desde-stdin.md").exists()


def test_buscar_sin_resultados_lo_dice_explicitamente(entorno, capsys):
    main(["buscar", "algo-que-no-existe-en-ninguna-nota"])
    assert "Sin resultados." in capsys.readouterr().out


def test_buscar_encuentra_por_texto_y_muestra_ruta_y_resumen(entorno, capsys):
    RepositorioNotasFilesystem(entorno).guardar(
        Nota.nueva("Sobre git rebase", "contenido", FuenteNota.CLI, resumen="un resumen")
    )

    main(["buscar", "rebase"])

    salida = capsys.readouterr().out
    assert "sobre-git-rebase.md" in salida
    assert "un resumen" in salida


def test_reorganizar_sin_notas_pendientes_lo_dice_explicitamente(entorno, capsys):
    # PROVEEDOR_LLM=mock -> ClasificadorNotasMock nunca propone
    # categoria, así que ni con notas de sobra debería moverse nada.
    repo = RepositorioNotasFilesystem(entorno)
    for i in range(6):
        repo.guardar(Nota.nueva(f"Nota {i}", "contenido", FuenteNota.CLI))

    main(["reorganizar"])

    assert "Nada que reorganizar todavía." in capsys.readouterr().out


def test_reorganizar_sin_aplicar_no_mueve_nada(entorno):
    repo = RepositorioNotasFilesystem(entorno)
    for i in range(6):
        repo.guardar(Nota.nueva(f"Nota {i}", "contenido", FuenteNota.CLI))

    main(["reorganizar"])

    assert all(n.categoria is None for n in repo.listar())
