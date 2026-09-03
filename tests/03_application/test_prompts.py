from application.prompts import PROMPT_GENERADOR, PROMPT_RESUMIDOR, prompt_clasificador


def test_prompt_generador_pide_espanol_y_formato_tutorial():
    assert "español" in PROMPT_GENERADOR
    assert "tutorial" in PROMPT_GENERADOR


def test_prompt_resumidor_pide_espanol_y_fidelidad_al_documento():
    assert "español" in PROMPT_RESUMIDOR
    assert "no añadas información" in PROMPT_RESUMIDOR.lower()


def test_prompt_clasificador_incluye_las_categorias_existentes():
    prompt = prompt_clasificador(["git", "git/commits"])
    assert "- git" in prompt
    assert "- git/commits" in prompt


def test_prompt_clasificador_sin_categorias_lo_deja_explicito():
    prompt = prompt_clasificador([])
    assert "ninguna todavía" in prompt
