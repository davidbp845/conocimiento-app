# conocimiento_app — contexto para Claude Code

Motor reutilizable (arquitectura hexagonal) para archivar conocimiento
tipo tutorial/procedimiento. Ver `README.md` para la estructura
completa, el formato de nota y las reglas de reorganización del árbol.

Este repo puede clonarse solo (usa su propio `vault_in/`/`vault_out/`
de ejemplo) o embeberse como submódulo git de otro repo que guarde ahí
su vault real — ver "Dos formas de usarlo" en `README.md` y
`config/paths.py`. Si estás trabajando desde el repo que lo embebe,
las reglas específicas de ese repo (dónde vive el vault real, qué
comandos expone) están en el `CLAUDE.md` de ese repo, no aquí.

## Reglas de este repo

- **Identificadores y docstrings en español**, dataclasses/ABC como en
  `domain/`, clases de caso de uso con `__init__` (dependencias) +
  `ejecutar()` (parámetros de la llamada) — mismo estilo en todo el
  proyecto, ver `/siguiente-pieza` para cómo continuarlo.
- **`domain/` no importa nada de `adapters/`, `config/` ni
  `streamlit_app/`.** Es la única capa que de verdad define "qué es"
  este proyecto; todo lo demás depende de ella, nunca al revés.
- **Las rutas (`.env`, `vault_in/`, `vault_out/`) se resuelven siempre
  vía `config/paths.py:home()`**, nunca con `"./vault_out"` ni
  `load_dotenv()` a secas — eso es lo que permite que este repo
  funcione igual standalone que embebido, sin depender de cuál sea el
  directorio de trabajo del proceso.
- **`vault_out/` de este repo es contenido de ejemplo**, no el vault
  real de nadie — no le añadas notas personales o sensibles aquí; para
  eso está el repo host cuando este proyecto se embebe como submódulo.
- Antes de dar una pieza por terminada: al menos un smoke test manual
  y, si la capa ya tiene carpeta en `tests/`, tests reales con pytest
  (ver `/siguiente-pieza`, paso 4).
