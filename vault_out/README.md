# vault_out

Aquí viven las notas ya redactadas: el conocimiento en sí, en Markdown
con frontmatter (ver formato en el README raíz del proyecto).

Las cuatro notas que trae este repo (`como-usar-docker-compose...`,
`guia-rapida-de-streamlit-session-state...`, y las dos de `git/`) son
**contenido de ejemplo**, pensado para que al clonar el repo el panel
Streamlit y la CLI tengan algo que mostrar desde el primer momento, no
una carpeta vacía. Sustitúyelas por tu propio contenido sin problema —
no las trates como si fueran una plantilla obligatoria.

Al principio todas las notas se guardan planas en esta misma carpeta
(sin subcarpetas). El comando `reorganizar` (ver README raíz) es el
único mecanismo que crea subcarpetas y mueve notas dentro de ellas,
siguiendo las reglas de crecimiento armonioso descritas allí — la
carpeta `git/` de este repo simula el resultado de esa reorganización
ya aplicada (en un vault real haría falta alcanzar antes el umbral
mínimo de notas afines). No muevas ni reclasifiques notas a mano si
puedes evitarlo: así el árbol siempre refleja una única fuente de
verdad (el comando), y no dos criterios distintos mezclados.

Este fichero (y esta carpeta) sí se versionan en git — es el
contenido de valor del proyecto (o, en este repo público, su ejemplo).
