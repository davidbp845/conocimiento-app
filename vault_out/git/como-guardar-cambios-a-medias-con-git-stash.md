---
titulo: "Cómo guardar cambios a medias con git stash"
tags: [git, cli]
categoria: git
fuente: claude_code
pregunta_origen: "tengo cambios sin terminar y necesito cambiar de rama ya — ¿cómo los aparco sin hacer un commit a medias?"
resumen: "git stash guarda los cambios sin confirmar en una pila aparte y deja el árbol de trabajo limpio, listo para recuperarlos después con git stash pop."
fecha: 2026-08-18
---

# Cómo guardar cambios a medias con git stash

```bash
git stash                 # guarda cambios trackeados, deja el árbol limpio
git stash -u               # + ficheros nuevos sin trackear
git stash list              # ver la pila de stashes guardados
git stash pop               # recupera el último y lo quita de la pila
git stash apply stash@{1}   # recupera uno concreto sin quitarlo de la pila
```

Útil cuando hay que cambiar de rama con trabajo a medias que no
merece un commit todavía (un experimento, una prueba rápida): `stash`
aparca los cambios en una pila independiente de las ramas y deja el
working tree como el último commit, así que `git checkout otra-rama`
ya no se queja de cambios sin confirmar.

Detalles que conviene saber:

- Por defecto **no incluye ficheros nuevos sin trackear** — hace falta
  `-u` (`--include-untracked`) para llevárselos también.
- `git stash pop` puede generar **conflictos** si la rama de destino
  ha cambiado las mismas líneas — se resuelven igual que un conflicto
  de merge normal (ver nota relacionada).
- Un stash no desaparece solo: si nunca haces `pop`/`drop`, se queda
  acumulado en la pila. `git stash clear` la vacía entera (sin
  posibilidad de deshacerlo).
- `git stash push -m "mensaje"` permite ponerle una descripción, útil
  si vas a tener más de un stash a la vez y `git stash list` sin
  contexto no basta para distinguirlos.

## Ver también

- [[como-revertir-el-ultimo-commit-sin-perder-los-cambios]]
- [[como-resolver-un-conflicto-de-merge-en-git]]
