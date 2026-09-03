---
description: Calcula (y, con --aplicar, ejecuta) el plan de reorganización de las notas planas de vault_out en subcarpetas
argument-hint: [--aplicar — opcional, si no se da es solo simulación]
---

Reorganiza `vault_out/` siguiendo al pie de la letra las reglas de "Crecimiento del árbol" del `README.md` raíz. El adaptador `adapters/in_/cli.py reorganizar` todavía no existe (ver "Estado actual" en README.md), así que aplica tú mismo la misma lógica que describe `domain/use_cases.py` (`PlanificarReorganizacion`/`AplicarReorganizacion`) directamente sobre los ficheros:

1. Lista las notas con `categoria: null` (planas en la raíz de `vault_out/`) — las ya clasificadas no se reconsideran.
2. Agrúpalas por temática coherente. Para cada grupo candidato a carpeta nueva:
   - Si la carpeta ya existe en `vault_out/`, puedes mover notas a ella sin umbral mínimo (ya está justificada).
   - Si la carpeta no existe todavía, solo la creas si el grupo reúne al menos 5 notas afines (umbral configurable, ver `UMBRAL_MINIMO_NOTAS_POR_CATEGORIA` en `domain/use_cases.py`). Si no llega, esas notas se quedan planas — no fuerces un grupo.
   - Ninguna carpeta puede quedar a más de 2 niveles de profundidad (`PROFUNDIDAD_MAXIMA_CATEGORIA`).
   - Cada nota va a una única carpeta candidata; si dudas entre dos, es señal de que la taxonomía no está lo bastante clara todavía — dilo en vez de elegir arbitrariamente.
3. Muestra el plan como tabla `nota -> carpeta destino` y **no muevas nada todavía**.
4. Solo si el argumento es `--aplicar`: mueve cada fichero a `vault_out/<carpeta>/<mismo-nombre>.md` y actualiza su `categoria` en el frontmatter al valor de la carpeta (ruta relativa, con `/` como separador). Si el repo ya tiene git inicializado, usa `git mv` en vez de `mv` para conservar el historial.
5. Si no hay notas pendientes o ningún grupo alcanza el umbral, dilo explícitamente y no crees ninguna carpeta.
