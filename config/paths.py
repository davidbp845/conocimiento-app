"""Resuelve dónde viven `.env`, `vault_in/`, `vault_out/` y
`conocimiento.yaml` sin depender de cuál sea el directorio de trabajo
desde el que se lance el proceso.

`conocimiento_app` funciona en dos escenarios:

1. **Standalone** (repo público clonado solo): usa su propio
   `vault_in/`/`vault_out/`/`.env` como raíz — los que trae de ejemplo.
2. **Embebido como submódulo** de un repo privado (p. ej. `conocimiento/`)
   que guarda ahí su vault real: ese repo exporta `CONOCIMIENTO_HOME`
   (ver su `start.sh`) apuntando a su propia raíz, fuera del submódulo.

Sin esta indirección, `load_dotenv()`/`./vault_out` (relativos al cwd)
solo funcionan si quien lanza el proceso hace `cd` a la carpeta
correcta primero — frágil en cuanto el proceso se lanza desde otro
sitio (una sesión de Claude Code, un systemd unit...)."""
from __future__ import annotations

import os
from pathlib import Path


def home() -> Path:
    variable = os.environ.get("CONOCIMIENTO_HOME")
    if variable:
        return Path(variable)
    return Path(__file__).resolve().parent.parent
