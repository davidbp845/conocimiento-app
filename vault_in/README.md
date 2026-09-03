# vault_in

Bandeja de entrada para `.md` pegados a mano, o volcados por el bot de
Telegram (`/iniciar`+`/finalizar`, ver "Bot de Telegram" en el README
raíz — ficheros `telegram-*.md`): sin frontmatter, o con frontmatter
incompleto (falta `titulo`, `resumen`, `tags`, `fecha`...). No es donde
vive el conocimiento ya archivado — para eso está `vault_out/`.

Dos formas de vaciarla hacia `vault_out/` (siempre con `fuente: manual`
y `categoria: null` — nunca decide `categoria`, eso es trabajo
exclusivo de `/reorganizar-vault`):

- `python -m adapters.in_.cli normalizar [--aplicar]` — automatizable
  (llama directo a la API de Anthropic, sin Claude Code de por medio),
  pensado para correr sin supervisión cada pocos minutos (ver
  despliegue en el README raíz).
- `/normalizar-vault-in [--aplicar]` desde una sesión de Claude Code —
  más lento, pero puede razonar caso a caso (fusionar turnos
  duplicados, separar temas mezclados) con más cuidado que una sola
  llamada al LLM.

Esta carpeta viene vacía a propósito en este repo (a diferencia de
`vault_out/`, que sí trae notas de ejemplo): su contenido es siempre
transitorio por diseño, así que no hay un estado de "ejemplo"
representativo que mostrar aquí.
