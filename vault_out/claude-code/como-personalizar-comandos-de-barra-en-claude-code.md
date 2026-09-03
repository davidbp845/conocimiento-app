---
titulo: "Cómo personalizar comandos de barra en Claude Code"
tags: [claude-code, ia]
categoria: claude-code
fuente: claude_code
pregunta_origen: "quiero un comando propio tipo /mi-comando en Claude Code para este proyecto — ¿cómo lo creo?"
resumen: "un fichero .md en .claude/commands/ con frontmatter (description, argument-hint) e instrucciones en el cuerpo se convierte en /nombre-del-fichero."
fecha: 2026-08-30
---

# Cómo personalizar comandos de barra en Claude Code

Un comando de barra (`/nombre`) es, literalmente, un fichero Markdown:

```
.claude/commands/nombre-del-comando.md
```

```markdown
---
description: Qué hace este comando, en una frase
argument-hint: [argumento esperado — opcional]
---

Instrucciones en lenguaje natural de lo que Claude debe hacer al
invocar /nombre-del-comando. "$1" se sustituye por el primer argumento
que pase quien lo invoque.
```

Puntos prácticos:

- El **nombre del fichero** (sin `.md`) es el nombre del comando —
  `nueva-tarea.md` se invoca como `/nueva-tarea`.
- `description` es lo que aparece al listar comandos disponibles
  (autocompletado, o un comando tipo `/ayuda` que los recorra).
- `argument-hint` es solo documentación para quien lo invoca — no
  valida nada por sí solo; si el comando exige un argumento, hay que
  decirlo en las instrucciones del cuerpo, no solo en el hint.
- `"$1"`, `"$2"`... referencian los argumentos posicionales pasados al
  invocar el comando; si no se pasa ninguno, las instrucciones deben
  decir explícitamente qué hacer en ese caso (pedirlo, usar un valor
  por defecto, elegirlo con criterio propio).
- Los comandos son simplemente ficheros del repo: se versionan en git
  como cualquier otro, y viajan con el proyecto a quien lo clone.

## Ver también

- [[diferencia-entre-un-hook-y-un-comando-de-barra-en-claude-code]]
