---
description: Busca notas en vault_out por texto y/o tag y resume los resultados
argument-hint: [texto a buscar, o #tag]
---

Busca "$1" en `vault_out/` (recursivo, incluye subcarpetas ya reorganizadas):

1. Si "$1" empieza por `#`, trátalo como tag: busca coincidencia exacta en el campo `tags` del frontmatter. Si no, búscalo como texto libre en `titulo`, `resumen`, `tags` y el cuerpo de cada nota.
2. Para cada coincidencia, muestra: ruta relativa dentro de `vault_out/`, `titulo`, `resumen` y `tags` — no pegues el cuerpo entero de la nota salvo que el usuario pida ver una en concreto.
3. Si no hay resultados, dilo explícitamente en vez de forzar coincidencias parciales poco relacionadas.
4. Esto es de solo lectura: no edites ni muevas ninguna nota (para eso está `/reorganizar-vault`).
