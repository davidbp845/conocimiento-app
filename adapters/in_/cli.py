"""CLI: `python -m adapters.in_.cli <subcomando>`. Construye su propia
instancia mínima de las piezas que necesita en vez de compartir la
composition root de main.py (mismo criterio que scripts/obsidian_ingest.py
en el proyecto hermano orquestador: un comando de un solo uso no debe
crear una dependencia circular entre adapters/in_ y main.py)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import frontmatter
from dotenv import load_dotenv

from adapters.out.repositorio_notas_filesystem import RepositorioNotasFilesystem
from config.paths import home
from domain.use_cases import (
    AplicarReorganizacion,
    ArchivarNotaRedactada,
    BuscarNotas,
    PlanificarReorganizacion,
)

load_dotenv(home() / ".env")


def _proveedor_llm() -> str:
    return os.environ.get("PROVEEDOR_LLM", "anthropic")


def _repositorio() -> RepositorioNotasFilesystem:
    return RepositorioNotasFilesystem(os.environ.get("VAULT_OUT_PATH", str(home() / "vault_out")))


def _generador():
    if _proveedor_llm() == "mock":
        from adapters.out.llm_mock import GeneradorRespuestasMock
        return GeneradorRespuestasMock()
    from adapters.out.llm_anthropic import GeneradorRespuestasAnthropic
    return GeneradorRespuestasAnthropic()


def _clasificador():
    if _proveedor_llm() == "mock":
        from adapters.out.llm_mock import ClasificadorNotasMock
        return ClasificadorNotasMock()
    from adapters.out.llm_anthropic import ClasificadorNotasAnthropic
    return ClasificadorNotasAnthropic()


def _cmd_guardar(args: argparse.Namespace) -> None:
    crudo = sys.stdin.read() if args.stdin else Path(args.archivo).read_text(encoding="utf-8")

    # El texto puede traer ya su propio frontmatter (redactado a mano,
    # o por /guardar-respuesta en Claude Code) — si lo trae, se
    # respeta; si no, el título sale de la primera línea no vacía.
    post = frontmatter.loads(crudo)
    titulo = post.get("titulo") or next(
        (linea.lstrip("# ").strip() for linea in post.content.splitlines() if linea.strip()),
        "Nota sin título",
    )

    nota = ArchivarNotaRedactada(_repositorio()).ejecutar(
        titulo=titulo,
        contenido=post.content,
        tags=post.get("tags"),
        pregunta_origen=post.get("pregunta_origen"),
        resumen=post.get("resumen"),
    )
    print(f"Guardada: vault_out/{nota.id}.md")


def _cmd_buscar(args: argparse.Namespace) -> None:
    notas = BuscarNotas(_repositorio()).ejecutar(texto=args.texto, tags=args.tag)
    if not notas:
        print("Sin resultados.")
        return
    for nota in notas:
        ruta = f"{nota.categoria}/{nota.id}.md" if nota.categoria else f"{nota.id}.md"
        print(f"- {ruta} — {nota.titulo}")
        if nota.resumen:
            print(f"    {nota.resumen}")


def _cmd_reorganizar(args: argparse.Namespace) -> None:
    repo = _repositorio()
    plan = PlanificarReorganizacion(repo, _clasificador()).ejecutar()
    if not plan:
        print("Nada que reorganizar todavía.")
        return

    for movimiento in plan:
        origen = movimiento.categoria_actual or "(raíz)"
        print(f"{movimiento.nota_id}: {origen} -> {movimiento.categoria_propuesta}")

    if args.aplicar:
        AplicarReorganizacion(repo).ejecutar(plan)
        print(f"\nAplicado: {len(plan)} nota(s) movidas.")
    else:
        print("\n(simulación: pasa --aplicar para ejecutar este plan)")


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m adapters.in_.cli")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_guardar = subparsers.add_parser("guardar", help="Archiva una nota ya redactada")
    origen = p_guardar.add_mutually_exclusive_group(required=True)
    origen.add_argument("--archivo", help="Ruta a un fichero .md ya redactado")
    origen.add_argument("--stdin", action="store_true", help="Lee el markdown de la entrada estándar")
    p_guardar.set_defaults(func=_cmd_guardar)

    p_buscar = subparsers.add_parser("buscar", help="Busca notas por texto y/o tag")
    p_buscar.add_argument("texto", nargs="?", default=None)
    p_buscar.add_argument("--tag", action="append", help="Repetible: --tag git --tag cli")
    p_buscar.set_defaults(func=_cmd_buscar)

    p_reorganizar = subparsers.add_parser(
        "reorganizar", help="Calcula (y con --aplicar, ejecuta) el plan de reorganización"
    )
    p_reorganizar.add_argument("--aplicar", action="store_true")
    p_reorganizar.set_defaults(func=_cmd_reorganizar)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = _construir_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
