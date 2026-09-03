---
titulo: "Diferencia entre git rebase y git merge"
tags: [git, cli]
categoria: git
fuente: claude_code
pregunta_origen: "¿cuándo conviene usar rebase en vez de merge?"
resumen: "merge conserva el historial real con un commit de fusión; rebase lo reescribe como si tu rama hubiera partido del HEAD actual."
fecha: 2026-08-25
---

# Diferencia entre git rebase y git merge

Ambos integran los cambios de una rama en otra, pero de formas
distintas:

**`git merge otra-rama`**
- Crea un commit de fusión nuevo con dos padres.
- El historial refleja exactamente lo que pasó: cuándo divergieron las
  ramas y cuándo se juntaron.
- Seguro en ramas compartidas — nunca reescribe commits existentes.

**`git rebase otra-rama`**
- Reaplica, uno a uno, los commits de tu rama actual encima del último
  commit de `otra-rama`.
- El historial queda lineal, como si hubieras empezado a trabajar
  desde ahí — más limpio de leer, pero **reescribe** los hashes de tus
  commits.
- Nunca hagas rebase de una rama que otros ya han descargado, salvo
  que avises (`git push --force-with-lease` después) — reescribe
  historial que ellos ya tienen.

Regla práctica: `rebase` para limpiar tu propia rama de feature antes
de abrir un PR (historial lineal, fácil de revisar); `merge` para
integrar esa rama ya terminada en `main` (conserva el punto exacto de
integración, y no reescribe nada compartido).
