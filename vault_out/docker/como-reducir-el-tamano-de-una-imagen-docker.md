---
titulo: "Cómo reducir el tamaño de una imagen Docker"
tags: [docker, cli]
categoria: docker
fuente: claude_code
pregunta_origen: "mi imagen Docker pesa más de 1GB para una app de Python bastante simple — ¿cómo la hago más pequeña?"
resumen: "imagen base slim/alpine, multi-stage build y un .dockerignore completo son las tres mejoras con más impacto en el tamaño final."
fecha: 2026-08-24
---

# Cómo reducir el tamaño de una imagen Docker

Tres cambios que suelen dar la mayor reducción, de más a menos impacto
típico:

1. **Imagen base más pequeña.** `python:3.12` (~1GB) trae herramientas
   de compilación y librerías que casi nunca hacen falta en producción.
   `python:3.12-slim` (~150MB) o `python:3.12-alpine` (~50MB, pero usa
   `musl` en vez de `glibc` — algunas dependencias con extensiones C
   compiladas pueden fallar o necesitar recompilarse) cubren la mayoría
   de casos.

2. **Multi-stage build**: separar la etapa que instala dependencias de
   compilación (necesarias solo para *construir* algunas librerías) de
   la imagen final, que solo necesita el resultado ya compilado:

   ```dockerfile
   FROM python:3.12-slim AS build
   RUN pip install --user -r requirements.txt

   FROM python:3.12-slim
   COPY --from=build /root/.local /root/.local
   COPY . .
   CMD ["python", "main.py"]
   ```

   La imagen final nunca ve el compilador ni las cabeceras de
   desarrollo que la etapa `build` sí necesitó.

3. **`.dockerignore` completo** (`.git/`, `venv/`, `__pycache__/`,
   `tests/`, `*.md`...) — sin él, `COPY . .` mete en la imagen todo lo
   que hay en el directorio, aunque no se use en tiempo de ejecución.

Para medir el efecto real: `docker images` muestra el tamaño de cada
imagen, y `docker history mi-imagen` desglosa cuánto pesa cada capa —
útil para ver exactamente qué instrucción del `Dockerfile` está
inflando el resultado antes de optimizarla a ciegas.

## Ver también

- [[diferencia-entre-dockerfile-y-docker-compose]]
