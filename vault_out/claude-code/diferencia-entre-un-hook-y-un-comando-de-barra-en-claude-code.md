---
titulo: "Diferencia entre un hook y un comando de barra en Claude Code"
tags: [claude-code, ia]
categoria: claude-code
fuente: claude_code
pregunta_origen: "tengo un /comando y un hook que hacen algo parecido — ¿cuándo uso cada uno?"
resumen: "un comando de barra lo invoca la persona, a propósito, cuando quiere; un hook lo dispara el propio harness automáticamente en un evento (antes/después de una herramienta, al terminar...), sin que nadie lo pida cada vez."
fecha: 2026-08-31
---

# Diferencia entre un hook y un comando de barra en Claude Code

**Comando de barra (`/nombre`)**
- Lo invoca explícitamente la persona, cuando quiere.
- Es un fichero Markdown con instrucciones en lenguaje natural (ver
  nota relacionada) — Claude las lee y las sigue como el resto de la
  conversación.
- Encaja en tareas que tienen sentido bajo demanda: archivar una nota,
  buscar algo, reorganizar una carpeta.

**Hook**
- Lo dispara automáticamente el harness en un evento del ciclo de vida
  (antes de ejecutar una herramienta, después de que Claude responda,
  al arrancar la sesión...), sin que nadie lo pida cada vez.
- Se configura declarativamente (típicamente en un `settings.json`),
  no como un `.md` con instrucciones en lenguaje natural — un hook
  suele ejecutar un comando de shell fijo, no "razonar" sobre qué
  hacer.
- Encaja en reglas que deben cumplirse siempre, automáticamente: un
  linter antes de aceptar una edición, una notificación al terminar
  una tarea larga, un bloqueo de cierto comando peligroso.

Regla práctica: si la respuesta a "¿quién decide cuándo pasa esto?" es
"la persona, cada vez que le interesa" → comando de barra. Si es
"siempre que ocurra X, automáticamente, sin que nadie tenga que
acordarse de pedirlo" → hook.

## Ver también

- [[como-personalizar-comandos-de-barra-en-claude-code]]
