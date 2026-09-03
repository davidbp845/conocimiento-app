---
titulo: "Cómo revertir el último commit sin perder los cambios"
tags: [git, cli]
categoria: git
fuente: claude_code
pregunta_origen: "¿cómo deshago el último commit pero me quedo con los cambios en el working tree?"
resumen: "git reset --soft HEAD~1 deshace el commit y deja los cambios staged."
fecha: 2026-08-20
---

# Cómo revertir el último commit sin perder los cambios

```bash
git reset --soft HEAD~1
```

Esto mueve `HEAD` (y la rama actual) al commit anterior, pero deja el
árbol de trabajo y el índice tal cual estaban — los cambios del commit
deshecho quedan **staged**, listos para volver a hacer `git commit`
con otro mensaje, dividirlos en varios commits, o añadir algo más antes
de confirmar.

Variantes según qué quieras conservar:

- `git reset --soft HEAD~1` — cambios staged (los ficheros modificados
  quedan en el índice, como recién hechos `git add`).
- `git reset --mixed HEAD~1` (por defecto, sin `--soft` ni `--hard`) —
  cambios en el árbol de trabajo pero *sin* stage, como si nunca
  hubieras hecho `git add`.
- `git reset --hard HEAD~1` — **descarta** los cambios del commit por
  completo. Solo si de verdad no los quieres.

Si el commit ya se ha subido a un remoto compartido, `reset` reescribe
historial — mejor `git revert HEAD`, que crea un commit nuevo que
deshace el anterior sin tocar los que ya existen.
