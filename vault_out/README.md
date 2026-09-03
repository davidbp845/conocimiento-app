# vault_out

Aquí viven las notas ya redactadas: el conocimiento en sí, en Markdown
con frontmatter (ver formato en el README raíz del proyecto).

Las doce notas que trae este repo son **contenido de ejemplo**,
organizado en cuatro categorías (`git/`, `docker/`, `streamlit/`,
`claude-code/`) más una nota-índice plana
(`notas-tecnicas-mas-consultadas.md`), pensado para que al clonar el
repo el panel Streamlit, la CLI **y el grafo de Obsidian** (si abres
esta carpeta, o `conocimiento_app/` entera, como vault) tengan algo
interesante que mostrar desde el primer momento, no una carpeta vacía
ni notas sueltas sin relación entre sí. Cada nota enlaza con
`[[wikilinks]]` a 1-2 notas relacionadas (sección "Ver también" al
final del cuerpo) y comparte tags con las de su misma categoría — con
el grafo de Obsidian activado, eso debería verse como cuatro grupos
conectados a la nota-índice, no como puntos sueltos. Sustituye todo
esto por tu propio contenido sin problema — no lo trates como una
plantilla obligatoria.

Al principio todas las notas se guardan planas en esta misma carpeta
(sin subcarpetas). El comando `reorganizar` (ver README raíz) es el
único mecanismo que crea subcarpetas y mueve notas dentro de ellas,
siguiendo las reglas de crecimiento armonioso descritas allí — las
carpetas de este repo no son una simulación a mano: son exactamente lo
que `reorganizar --aplicar` produce sobre estas notas ya clasificadas,
con el umbral mínimo de `config/conocimiento.yaml` bajado a 2 (en vez
del 5 por defecto) para que un ejemplo de este tamaño sea reproducible
de verdad — un vault real debería mantener el 5 por defecto. No muevas
ni reclasifiques notas a mano si puedes evitarlo: así el árbol siempre
refleja una única fuente de verdad (el comando), y no dos criterios
distintos mezclados.

Este fichero (y esta carpeta) sí se versionan en git — es el
contenido de valor del proyecto (o, en este repo público, su ejemplo).
