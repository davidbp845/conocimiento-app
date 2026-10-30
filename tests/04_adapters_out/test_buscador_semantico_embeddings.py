import json
import sys

from adapters.out.buscador_semantico_embeddings import BuscadorSemanticoEmbeddings, crear_buscador_semantico
from domain.entities import FuenteNota, Nota

# Embedder falso: cada texto se proyecta sobre unos ejes temáticos
# según las palabras que contiene, así dos textos con palabras del
# mismo grupo se parecen aunque no compartan ninguna.
EJES = [
    {"commit", "revertir", "deshacer", "git"},
    {"docker", "contenedor", "imagen"},
    {"receta", "cocina", "horno"},
]


class EmbedderFalso:
    def __init__(self):
        self.textos_recibidos: list[str] = []

    def __call__(self, textos: list[str]) -> list[list[float]]:
        self.textos_recibidos.extend(textos)
        return [self._vector(t) for t in textos]

    @staticmethod
    def _vector(texto: str) -> list[float]:
        palabras = set(texto.lower().replace("\n", " ").split())
        return [float(len(palabras & eje)) for eje in EJES]


def _nota(titulo: str, contenido: str = "", resumen: str | None = None) -> Nota:
    return Nota.nueva(titulo, contenido, FuenteNota.CLI, resumen=resumen)


def test_encuentra_por_significado_aunque_no_compartan_palabras(tmp_path):
    notas = [_nota("Cómo revertir el último commit"), _nota("Imagen de docker"), _nota("Receta al horno")]
    buscador = BuscadorSemanticoEmbeddings(EmbedderFalso(), tmp_path / "indice.json", umbral=0.5)

    resultado = buscador.buscar("deshacer git", notas)

    assert [nota_id for nota_id, _ in resultado] == ["como-revertir-el-ultimo-commit"]


def test_ordena_de_mayor_a_menor_puntuacion(tmp_path):
    notas = [_nota("docker y commit"), _nota("revertir commit")]
    buscador = BuscadorSemanticoEmbeddings(EmbedderFalso(), tmp_path / "indice.json", umbral=0.1)

    resultado = buscador.buscar("deshacer", notas)

    assert [nota_id for nota_id, _ in resultado] == ["revertir-commit", "docker-y-commit"]
    assert resultado[0][1] > resultado[1][1]


def test_no_recalcula_notas_sin_cambios_y_si_las_cambiadas(tmp_path):
    embedder = EmbedderFalso()
    buscador = BuscadorSemanticoEmbeddings(embedder, tmp_path / "indice.json")
    nota = _nota("revertir commit")
    buscador.buscar("git", [nota, _nota("docker")])

    embedder.textos_recibidos.clear()
    nota.contenido = "git revert HEAD"
    buscador.buscar("git", [nota, _nota("docker")])

    # La consulta, y solo la nota cuyo texto cambió.
    assert embedder.textos_recibidos == ["revertir commit\ngit revert HEAD", "git"]


def test_mover_una_nota_no_recalcula_su_vector(tmp_path):
    embedder = EmbedderFalso()
    buscador = BuscadorSemanticoEmbeddings(embedder, tmp_path / "indice.json")
    nota = _nota("revertir commit")
    buscador.buscar("git", [nota])

    embedder.textos_recibidos.clear()
    nota.categoria = "git"
    buscador.buscar("git", [nota])

    assert embedder.textos_recibidos == ["git"]


def test_quita_del_indice_las_notas_borradas(tmp_path):
    ruta = tmp_path / "indice.json"
    buscador = BuscadorSemanticoEmbeddings(EmbedderFalso(), ruta)
    buscador.buscar("git", [_nota("revertir commit"), _nota("docker")])

    buscador.buscar("git", [_nota("docker")])

    assert set(json.loads(ruta.read_text())["notas"]) == {"docker"}


def test_reconstruye_el_indice_entero_si_cambia_el_modelo(tmp_path):
    ruta = tmp_path / "indice.json"
    BuscadorSemanticoEmbeddings(EmbedderFalso(), ruta, modelo="viejo").buscar("git", [_nota("revertir commit")])

    embedder = EmbedderFalso()
    BuscadorSemanticoEmbeddings(embedder, ruta, modelo="nuevo").buscar("git", [_nota("revertir commit")])

    assert embedder.textos_recibidos == ["revertir commit", "git"]
    assert json.loads(ruta.read_text())["modelo"] == "nuevo"


def test_reconstruye_el_indice_si_esta_corrupto(tmp_path):
    ruta = tmp_path / "indice.json"
    ruta.write_text("{no es json")

    resultado = BuscadorSemanticoEmbeddings(EmbedderFalso(), ruta, umbral=0.5).buscar(
        "git", [_nota("revertir commit")]
    )

    assert [nota_id for nota_id, _ in resultado] == ["revertir-commit"]


def test_la_carpeta_del_indice_se_ignora_a_si_misma_en_git(tmp_path):
    ruta = tmp_path / ".cache" / "indice.json"

    BuscadorSemanticoEmbeddings(EmbedderFalso(), ruta).buscar("git", [_nota("revertir commit")])

    assert (ruta.parent / ".gitignore").read_text() == "*\n"


def test_indexa_titulo_resumen_y_contenido(tmp_path):
    embedder = EmbedderFalso()
    buscador = BuscadorSemanticoEmbeddings(embedder, tmp_path / "indice.json")

    buscador.buscar("git", [_nota("Título", "Contenido", resumen="Resumen")])

    assert embedder.textos_recibidos[0] == "Título\nResumen\nContenido"


def test_crear_buscador_semantico_devuelve_none_sin_sentence_transformers(tmp_path, monkeypatch):
    # None en sys.modules hace que `import sentence_transformers` lance
    # ImportError aunque esté instalado.
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)

    assert crear_buscador_semantico(tmp_path / "vault_out") is None
