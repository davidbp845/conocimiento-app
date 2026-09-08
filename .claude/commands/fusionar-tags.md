---
description: Detecta tags de vault_out que son variantes del mismo concepto (mismo texto normalizado, o muy parecidos) y calcula (o, con --aplicar, ejecuta) su fusión en una única forma canónica
argument-hint: [--aplicar — opcional, si no se da es solo simulación]
---

Limpia duplicados de tags en `vault_out/` — variantes de la misma
etiqueta escritas distinto (`heruka-flow` / `herukaflow`, `ci-cd` /
`cicd`) que si se dejan sueltas rompen la búsqueda por tag del panel
Streamlit (`cli.py buscar --tag`) y ensucian "Formato de una nota" del
`README.md` raíz. Es el mismo mecanismo que ya deben aplicar
`/normalizar-vault-in` y `/guardar-respuesta` al crear tags nuevos —
este comando es para limpiar los que ya se colaron antes de que
existiera esa comprobación.

1. Recorre todas las notas de `vault_out/*.md` (recursivo) y extrae la
   lista de `tags` del frontmatter de cada una parseando el YAML
   completo, no con una regex que solo case `tags: [...]` en una
   línea — el vault mezcla ese formato en línea con el de lista en
   bloque (`tags:` seguido de un `- tag` por línea), y una regex de
   una sola línea se salta silenciosamente todas las notas del segundo
   formato.
2. Normaliza cada tag para comparar (no para mostrar): minúsculas, sin
   acentos, todo lo que no sea `[a-z0-9]` eliminado (no colapsado a
   `-`, a diferencia del `slug()` de `domain/entities.py` — aquí
   interesa que `heruka-flow` y `herukaflow` normalicen exactamente
   igual).
3. Agrupa los tags cuyo normalizado coincide exactamente — son
   fusiones seguras, misma palabra escrita distinto (guion, sin guion,
   mayúsculas, espacio en vez de guion).
4. Señala aparte, sin fusionar automáticamente, pares de tags con
   normalizado *distinto* pero similitud textual alta (una letra de
   diferencia, mismo lema con/sin sufijo) como candidatos a revisión
   manual. No son necesariamente el mismo concepto — p. ej.
   `agentes`/`agentes-ia` o `estilos-de-pagina`/`saltos-de-pagina` se
   parecen como cadena pero son ideas distintas. Para cada candidato,
   lee el título/resumen de las notas que llevan cada tag y decide caso
   por caso si son el mismo concepto o no; nunca fusiones solo por
   parecido de cadena.
5. Para cada grupo a fusionar (los seguros del paso 3, más los que
   confirmes del paso 4), elige la forma canónica:
   - Prefiere la variante ya usada en más notas.
   - En empate, prefiere la forma con guiones entre palabras (estilo
     del resto del vault, ver tags ya archivados) sobre la forma
     pegada o con espacios sueltos.
6. Muestra el plan como tabla `variante(s) -> tag canónico` con las
   notas afectadas por cada fila, y **no toques nada todavía**.
7. Solo si el argumento es `--aplicar`: en cada nota afectada,
   sustituye la variante por el tag canónico dentro de `tags:` (si una
   nota ya tuviera las dos variantes a la vez, deja el canónico una
   sola vez, sin duplicarlo). No toques ningún otro campo del
   frontmatter ni el cuerpo.
8. Si no hay tags duplicados ni candidatos dudosos, dilo explícitamente
   y no toques nada.
