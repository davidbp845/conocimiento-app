from datetime import date

import pytest

from adapters.out.repositorio_notas_filesystem import RepositorioNotasFilesystem
from domain.entities import FuenteNota, Nota
from domain.exceptions import NotaNoExiste


@pytest.fixture
def repo(tmp_path):
    return RepositorioNotasFilesystem(tmp_path)


def _nota(titulo="Cómo usar git rebase", **kwargs):
    return Nota.nueva(titulo, "contenido de prueba", FuenteNota.CLI, **kwargs)


def test_guardar_y_obtener_devuelve_la_misma_nota(repo):
    original = _nota(tags=["git"], resumen="resumen", pregunta_origen="¿pregunta?")
    repo.guardar(original)

    leida = repo.obtener(original.id)

    assert leida == original


def test_guardar_nota_plana_queda_en_la_raiz(repo, tmp_path):
    repo.guardar(_nota())
    assert (tmp_path / "como-usar-git-rebase.md").exists()


def test_guardar_nota_con_categoria_crea_la_subcarpeta(repo, tmp_path):
    nota = _nota()
    nota.categoria = "git"
    repo.guardar(nota)
    assert (tmp_path / "git" / "como-usar-git-rebase.md").exists()


def test_obtener_nota_inexistente_devuelve_none(repo):
    assert repo.obtener("no-existe") is None


def test_listar_devuelve_todas_las_notas_guardadas(repo):
    repo.guardar(_nota("Nota uno"))
    repo.guardar(_nota("Nota dos"))
    assert {n.id for n in repo.listar()} == {"nota-uno", "nota-dos"}


def test_buscar_por_texto_en_titulo_contenido_y_resumen(repo):
    repo.guardar(_nota("Sobre git", resumen="rebase interactivo"))
    repo.guardar(_nota("Sobre docker"))

    assert [n.titulo for n in repo.buscar(texto="rebase")] == ["Sobre git"]


def test_buscar_por_tags_requiere_todos_los_tags(repo):
    repo.guardar(_nota("A", tags=["git", "cli"]))
    repo.guardar(_nota("B", tags=["git"]))

    assert [n.titulo for n in repo.buscar(tags=["git", "cli"])] == ["A"]


def test_listar_categorias_ignora_las_notas_planas(repo):
    plana = _nota("Plana")
    repo.guardar(plana)
    clasificada = _nota("Clasificada")
    clasificada.categoria = "git/commits"
    repo.guardar(clasificada)

    assert repo.listar_categorias() == ["git/commits"]


def test_mover_reubica_el_fichero_y_actualiza_categoria(repo, tmp_path):
    repo.guardar(_nota())

    repo.mover("como-usar-git-rebase", "git")

    assert not (tmp_path / "como-usar-git-rebase.md").exists()
    assert (tmp_path / "git" / "como-usar-git-rebase.md").exists()
    assert repo.obtener("como-usar-git-rebase").categoria == "git"


def test_mover_a_la_misma_categoria_no_hace_nada(repo, tmp_path):
    nota = _nota()
    nota.categoria = "git"
    repo.guardar(nota)
    ruta = tmp_path / "git" / "como-usar-git-rebase.md"
    mtime_antes = ruta.stat().st_mtime_ns

    repo.mover("como-usar-git-rebase", "git")

    assert ruta.stat().st_mtime_ns == mtime_antes


def test_mover_nota_inexistente_lanza_nota_no_existe(repo):
    with pytest.raises(NotaNoExiste):
        repo.mover("no-existe", "git")


def test_mover_deja_limpia_la_carpeta_origen_si_queda_vacia(repo, tmp_path):
    nota = _nota()
    nota.categoria = "git"
    repo.guardar(nota)

    repo.mover("como-usar-git-rebase", "docker")

    assert not (tmp_path / "git").exists()


def test_eliminar_borra_el_fichero(repo, tmp_path):
    repo.guardar(_nota())

    repo.eliminar("como-usar-git-rebase")

    assert not (tmp_path / "como-usar-git-rebase.md").exists()
    assert repo.obtener("como-usar-git-rebase") is None


def test_eliminar_nota_inexistente_lanza_nota_no_existe(repo):
    with pytest.raises(NotaNoExiste):
        repo.eliminar("no-existe")


def test_eliminar_deja_limpia_la_carpeta_si_queda_vacia(repo, tmp_path):
    nota = _nota()
    nota.categoria = "git"
    repo.guardar(nota)

    repo.eliminar("como-usar-git-rebase")

    assert not (tmp_path / "git").exists()


def test_frontmatter_persistido_usa_los_campos_documentados_en_readme(repo, tmp_path):
    repo.guardar(_nota(tags=["git"], resumen="resumen", pregunta_origen="¿pregunta?"))
    texto = (tmp_path / "como-usar-git-rebase.md").read_text(encoding="utf-8")

    assert "titulo:" in texto
    assert "tags:" in texto
    assert "categoria:" in texto
    assert "fuente: cli" in texto
    assert "pregunta_origen:" in texto
    assert "resumen:" in texto
    assert f"fecha: {date.today().isoformat()}" in texto
