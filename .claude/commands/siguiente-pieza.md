---
description: Implementa la siguiente pieza pendiente de la arquitectura hexagonal, siguiendo el orden y el estilo ya establecidos
argument-hint: [pieza concreta a implementar — opcional, si no se da eliges tú la siguiente en orden]
---

Continúa la implementación de este proyecto siguiendo el mismo patrón usado hasta ahora (`domain/entities.py`, `domain/ports.py`, `domain/use_cases.py`), inspirado en los proyectos hermanos `orquestador` y `heruka-life`.

1. Lee la sección "Estado actual" de `README.md` y el contenido real de `domain/`, `application/`, `adapters/`, `config/` para confirmar qué existe ya y qué falta — no te fíes solo del README si el código ha avanzado más (o menos) de lo que dice.
2. Si se da "$1", implementa esa pieza concreta. Si no, elige la siguiente en orden de dependencia: `domain/exceptions.py` (solo si ya hace falta una excepción real, no de adelanto) → `config/` (schema.py + loader.py + conocimiento.yaml) → `application/` (orquestador.py, prompts.py) → `adapters/out/` (empezando por `repositorio_notas_filesystem.py`, es el que todo lo demás necesita para poder probarse) → `adapters/in_/` (cli.py antes que telegram_bot.py: no depende de credenciales externas) → `main.py` → `streamlit_app/app.py` → `tests/`.
3. Mantén el estilo ya usado: identificadores y docstrings en español, dataclasses/ABC como en `domain/`, clases de caso de uso con `__init__` (dependencias) + `ejecutar()` (parámetros de la llamada), comentarios que expliquen el *porqué* de una decisión no obvia y no el qué. No implementes nada que no esté ya descrito en README.md/domain/ — si hace falta decidir algo no documentado (p. ej. qué campos lleva `config/conocimiento.yaml`), pregunta o decide y documenta la decisión en README.md, no la dejes implícita solo en el código.
4. Verifica lo que implementes: al menos un import + smoke test manual (`python3 -c "..."`, como el resto del proyecto); si la pieza ya tiene su carpeta numerada en `tests/`, añade tests reales con pytest ahí en vez de solo el smoke test manual.
5. Actualiza la línea "Estado actual" de `README.md` para reflejar lo que acabas de añadir.
6. Implementa una sola pieza por invocación, salvo que el usuario pida explícitamente varias.
