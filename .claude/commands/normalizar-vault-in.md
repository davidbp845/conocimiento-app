---
description: Detecta los .md de vault_in/ con frontmatter ausente o incompleto o con el texto aplanado al pegar en Telegram, arregla ambas cosas y los traslada normalizados a vault_out/
argument-hint: [--aplicar — opcional, si no se da es solo simulación]
---

Normaliza los `.md` pegados a mano en `vault_in/` (ver "vault_in/" en
`README.md` raíz y `vault_in/README.md`) y los traslada a `vault_out/`
con el frontmatter completo. No hay adaptador ni caso de uso de
dominio para esto todavía (ver "Estado actual" en README.md), así que
aplica la lógica a mano, igual que ya hacen `/guardar-respuesta` y
`/reorganizar-vault`.

1. Lista los `.md` de `vault_in/` (recursivo). Ignora cualquier
   `README.md` — es documentación de la carpeta, no una nota.
2. Para cada fichero, lee su contenido crudo y separa frontmatter YAML
   (si existe) del cuerpo Markdown.
3. Antes de tocar el frontmatter, revisa si el cuerpo llegó aplanado —
   señal típica de un copia-pega desde una conversación de ChatGPT/Claude
   a un canal de Telegram, que se come los saltos de línea y convierte
   cualquier `/palabra` en un enlace `tg://bot_command?command=palabra`.
   Indicios: párrafos larguísimos en una sola línea, ausencia casi total
   de saltos de línea en un fichero de varios miles de caracteres, o
   presencia de enlaces `tg://bot_command`. Si detectas esto, reformatea
   el cuerpo antes de continuar:
   - Restaura los saltos de párrafo según los cambios de tema/idea.
   - Convierte en listas (`-`, `1.`) las enumeraciones que quedaron
     corridas en prosa.
   - Reconstruye en bloques de código los diagramas ASCII (líneas con
     `│ ├── └── ┌ ┐ ┴`) que hayan perdido sus saltos de línea; si la
     reconstrucción exacta no es recuperable, dilo explícitamente en el
     propio diagrama o cerca de él en vez de inventar una estructura
     con más precisión de la que el texto permite.
   - Deshaz los enlaces `[/palabra](tg://bot_command?...)` — únelos con
     el texto que los siga (p. ej. `[/memoria](tg://bot_command?...)`
     seguido de `-semantica` vuelve a ser `/memoria-semantica`) y
     déjalos como texto plano o `` `código` ``, no como enlace.
   - No inventes contenido nuevo. Si un tramo de la conversación falta
     por completo (p. ej. un turno de usuario que el aplanado se comió
     sin dejar rastro), señálalo con una nota entre paréntesis en vez de
     rellenarlo.
   - Si el fichero tiene varios turnos (el usuario va afinando la
     pregunta o añade contexto — "soy autónomo y alquilo cabina en
     Mataró", "el precio de la cabina es tal") y la IA responde
     repitiendo una versión anterior de su respuesta ya dada, ahora
     retocada con ese nuevo dato en vez de una respuesta realmente
     nueva, fusiona esos fragmentos en vez de dejarlos duplicados:
     - Detéctalo por solapamiento real de contenido (mismas frases,
       mismos puntos/listas, mismo orden de ideas), no solo porque el
       tema se repita — dos turnos sobre el mismo asunto pero con
       información distinta (p. ej. un caso general y luego un caso
       concreto con datos nuevos) no son una repetición y no se
       fusionan.
     - Al fusionar, conserva la versión más completa/afinada de cada
       punto (la que ya incorpora el dato nuevo) y descarta la anterior,
       manteniendo el hilo narrativo de por qué cambió (qué dato aportó
       el usuario que motivó el ajuste), no solo el resultado final.
     - Dilo explícitamente con una nota entre paréntesis cerca de la
       fusión (p. ej. "aquí se ha fusionado con la respuesta anterior,
       que repetía este punto ya retocado con el dato de que..."), del
       mismo modo que ya se señalan los tramos que faltan por completo.
   - Si el fichero mezcla turnos sobre temas realmente distintos, sin
     relación con el asunto principal de la nota (probablemente se
     pegaron juntos por venir de la misma conversación de Telegram,
     no porque pertenezcan al mismo tema), sepáralos en vez de
     archivarlos juntos:
     - Detéctalo por cambio de tema real, no de subtema. Dos turnos
       sobre la misma pregunta de fondo (p. ej., dentro de "qué
       alimentos comprar", pasar de comparar tipos de arroz a rankear
       conservas de pescado) siguen siendo la misma nota y no se
       separan. Un turno que cambia de naturaleza (de "qué comprar" a
       "cómo se cocina algo", de una lista de ideas a una pregunta de
       procedimiento suelta) sí se separa, aunque mencione elementos
       de la lista.
     - Extrae ese turno (pregunta reconstruida + respuesta, ya con el
       cuerpo reformateado según los puntos anteriores) a un fichero
       `.md` nuevo y descriptivo dentro de `vault_in/`, sin frontmatter
       — queda pendiente de su propia pasada de `/normalizar-vault-in`
       en vez de forzarlo dentro de una nota a la que no pertenece.
     - Señálalo en el plan (paso 6) y en el informe final: qué turno se
       separó, por qué, y a qué fichero nuevo de `vault_in/` fue a
       parar.
   - Si el fichero ya tiene saltos de línea y estructura razonable, no
     lo toques — este paso es solo para el caso de texto realmente
     aplanado.
4. Compara el frontmatter contra los campos documentados en "Formato de
   una nota" del README.md raíz: `titulo`, `tags`, `categoria`, `fuente`,
   `pregunta_origen`, `resumen`, `fecha`. No toques ningún campo que ya
   tenga un valor válido — completa solo lo que falte o esté vacío:
   - `titulo`: si falta, no te limites a copiar el primer encabezado
     `# ...` literal — optimízalo:
     - Quita prefijos de relleno conversacional ("Aquí tienes",
       "Claro,", "Sí.", "Buena pregunta"...) y puntuación sobrante.
     - Sé específico en vez de genérico: si el contenido trata un caso
       concreto (una ciudad, una tecnología, un negocio, una decisión),
       que el título lo refleje — nada de "Ideas para el negocio" o
       "Análisis de mercado" a secas si hay un tema más preciso.
     - Apunta a un titular breve (orientativamente 50-70 caracteres);
       si el encabezado original es más largo, resúmelo sin perder el
       tema central, sin cortarlo a mitad de una idea.
     - Usa el mismo registro que los títulos ya archivados en
       `vault_out/`: frase descriptiva en minúsculas salvo nombres
       propios, o pregunta si el contenido responde a una pregunta
       concreta (ver `pregunta_origen` más abajo).
     - Si no hay ningún encabezado en el cuerpo, deriva el título
       siguiendo estos mismos criterios a partir del contenido.
   - `fecha`: si falta, la fecha de hoy (`AAAA-MM-DD`).
   - `categoria`: si falta, déjala en `null`. No la infieras nunca
     aquí — es trabajo exclusivo de `/reorganizar-vault` (misma regla
     que sigue `/guardar-respuesta`: una sola fuente de verdad para
     dónde vive cada nota).
   - `fuente`: si falta, `manual`. Si ya tiene un valor válido de
     `FuenteNota` (`domain/entities.py`: `telegram`, `cli`,
     `claude_code`, `streamlit`, `manual`), respétalo tal cual.
   - `resumen`: si falta, una frase que resuma el contenido.
   - `tags`: si faltan o están vacías, entre 2 y 4 tags en minúsculas
     que reflejen el tema, con el mismo estilo que las notas ya
     archivadas en `vault_out/`.
   - `pregunta_origen`: si falta:
     - Si el cuerpo es claramente la respuesta directa de una IA a una
       pregunta que no aparece en el texto (empieza con "Sí.", "Claro,",
       entra directo en materia, responde en segunda persona a algo no
       escrito...), infiere una pregunta razonable y concisa que esa
       respuesta estaría contestando, y guárdala en `pregunta_origen`.
       Añade una nota entre paréntesis cerca (en la nota introductoria
       de reformateo del paso 3, o si no la hay, justo debajo del
       frontmatter) dejando claro que es una pregunta reconstruida y no
       la que realmente se escribió (p. ej. "`pregunta_origen` es una
       reconstrucción a partir del contenido; la pregunta real no
       estaba en el texto pegado").
     - Si el cuerpo no es conversacional (es una nota expositiva, unos
       apuntes, una lista de recursos... sin forma de respuesta a algo),
       no inventes una pregunta forzada — déjalo en `null`.
5. Calcula el id/fichero final igual que `domain/entities.py:slug()` a
   partir del `titulo` (ya existente o inferido): minúsculas, sin
   acentos, todo lo que no sea `[a-z0-9]` colapsado a un único `-`,
   recortado a 60 caracteres, sin `-` al principio/final. Si
   `vault_out/<slug>.md` ya existe, añade un sufijo numérico (`-2`,
   `-3`...) en vez de sobrescribir (igual que `/guardar-respuesta`).
6. Muestra el plan como tabla `vault_in/<fichero> -> vault_out/<slug>.md`
   con los campos que se van a añadir/inferir en cada nota (y si el
   cuerpo se va a reformatear por el paso 3), y **no toques nada
   todavía**. Si el paso 3 detectó algún turno fuera de tema, añádelo
   al plan como una fila aparte: `vault_in/<fichero> -> vault_in/<fichero
   nuevo>.md` (sin pasar por `vault_out/`), con el motivo de la
   separación.
7. Solo si el argumento es `--aplicar`: escribe cada nota completa en
   `vault_out/<slug>.md` (frontmatter documentado + cuerpo — reformateado
   según el paso 3 si aplicaba, intacto en caso contrario, y sin los
   turnos que el paso 3 haya separado por ir fuera de tema) y borra el
   fichero original de `vault_in/`. Si el repo tiene git inicializado,
   usa `git mv`/`git add` en vez de mover a mano para conservar el
   historial. Cada turno separado por ir fuera de tema se escribe como
   fichero nuevo dentro de `vault_in/` (no se archiva en `vault_out/`
   en esta misma pasada) y se menciona en el informe final: qué se
   separó, por qué, y el nombre del fichero nuevo.
8. Si `vault_in/` no tiene ningún `.md` pendiente (aparte de
   `README.md`), dilo explícitamente y no hagas nada.
