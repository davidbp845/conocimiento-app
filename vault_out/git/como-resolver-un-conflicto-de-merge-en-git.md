---
titulo: "Cómo resolver un conflicto de merge en git"
tags: [git, cli]
categoria: git
fuente: claude_code
pregunta_origen: "me ha saltado un conflicto haciendo merge (o rebase, o stash pop) y no sé qué hacer con las marcas raras que han aparecido en el fichero"
resumen: "los marcadores <<<<<<</=======/>>>>>>> señalan las dos versiones en conflicto; se edita a mano el resultado final y se marca resuelto con git add."
fecha: 2026-08-27
---

# Cómo resolver un conflicto de merge en git

Cuando `git merge`, `git rebase` o `git stash pop` no pueden combinar
dos cambios automáticamente (tocan las mismas líneas de formas
distintas), dejan el fichero con marcadores de conflicto:

```
<<<<<<< HEAD
tu versión actual
=======
la versión que se está integrando
>>>>>>> nombre-de-la-otra-rama
```

Pasos para resolverlo:

1. Abre cada fichero en conflicto (`git status` los lista bajo "Unmerged
   paths") y decide el contenido final — puede ser una de las dos
   versiones, una combinación de ambas, o algo distinto.
2. Borra los tres marcadores (`<<<<<<<`, `=======`, `>>>>>>>`) — dejarlos
   en el fichero por descuido es el error más común, y no da ningún
   error hasta que alguien nota código roto.
3. `git add <fichero>` marca ese fichero como resuelto (no hace commit
   todavía, solo lo saca de la lista de conflictos pendientes).
4. Cuando no quede ningún fichero en conflicto: `git commit` (en un
   merge) o `git rebase --continue` (en un rebase) para terminar la
   operación.

Si te bloqueas y prefieres no seguir: `git merge --abort` o `git
rebase --abort` devuelven el repo exactamente al estado anterior a
empezar, sin dejar nada a medias.

## Ver también

- [[diferencia-entre-git-rebase-y-git-merge]]
- [[como-guardar-cambios-a-medias-con-git-stash]]
