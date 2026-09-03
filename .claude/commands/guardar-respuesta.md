---
description: Archiva la última respuesta sustancial de esta conversación como una nota nueva en vault_out
argument-hint: [título de la nota — opcional, si no lo das lo propongo yo]
---

Archiva como nota de `vault_out/` la respuesta tipo tutorial/procedimiento más reciente de esta conversación (o la que el usuario señale). Los adaptadores todavía no existen (ver "Estado actual" en `README.md`), así que hazlo a mano siguiendo exactamente el formato que documenta el README:

1. Si no se da "$1", propón un título breve y descriptivo a partir de la respuesta a archivar; confírmalo con el usuario solo si es ambiguo qué respuesta archivar (por ejemplo, si ha habido varias respuestas sustanciales seguidas).
2. Calcula el id/fichero igual que `domain/entities.py:slug()`: minúsculas, sin acentos, todo lo que no sea `[a-z0-9]` colapsado a un único `-`, recortado a 60 caracteres, sin `-` al principio/final. Si `vault_out/<slug>.md` ya existe, añade un sufijo numérico (`-2`, `-3`...) en vez de sobrescribir.
3. Escribe `vault_out/<slug>.md` con el frontmatter documentado en README.md:
   ```yaml
   titulo: "..."
   tags: [...]
   categoria: null
   fuente: claude_code
   pregunta_origen: "..."   # la pregunta o petición que originó la respuesta, si la hay
   resumen: "..."           # una frase
   fecha: AAAA-MM-DD        # fecha de hoy
   ```
   seguido del cuerpo Markdown de la respuesta (limpio: sin las partes conversacionales tipo "claro, aquí tienes", directo al contenido).
4. No la muevas a ninguna subcarpeta ni inventes una `categoria` — eso es trabajo exclusivo de `/reorganizar-vault`, no de este comando (regla 1 de "Crecimiento del árbol" en README.md: una sola fuente de verdad para dónde vive cada nota).
5. Confirma con la ruta del fichero creado y el resumen de una línea.
