# vault_in

Bandeja de entrada para `.md` pegados a mano, o volcados por el bot de
Telegram (`/iniciar`+`/finalizar`, ver "Bot de Telegram" en el README
raíz — ficheros `telegram-*.md`): sin frontmatter, o con frontmatter
incompleto (falta `titulo`, `resumen`, `tags`, `fecha`...). No es donde
vive el conocimiento ya archivado — para eso está `vault_out/`.

El comando `/normalizar-vault-in` (`.claude/commands/`) recorre esta
carpeta, completa en cada fichero lo que le falte según el formato
documentado en el README raíz ("Formato de una nota"), y lo traslada
ya normalizado a `vault_out/` con `fuente: manual` — deja `vault_in/`
vacía cuando termina. Nunca decide `categoria`: la nota llega plana a
la raíz de `vault_out/`, igual que hace `ResponderYArchivar`; eso es
trabajo exclusivo de `/reorganizar-vault`.

Esta carpeta viene vacía a propósito en este repo (a diferencia de
`vault_out/`, que sí trae notas de ejemplo): su contenido es siempre
transitorio por diseño, así que no hay un estado de "ejemplo"
representativo que mostrar aquí.

No hay adaptador ni caso de uso de dominio para esto todavía (ver
"Estado actual" en el README raíz) — el comando aplica la lógica a
mano, como ya hacen `/guardar-respuesta` y `/reorganizar-vault`.
