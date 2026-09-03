---
titulo: "Cómo usar docker compose para levantar varios servicios"
tags: [docker, cli]
categoria: null
fuente: claude_code
pregunta_origen: "tengo una app con backend, base de datos y un worker — ¿cómo lo levanto todo junto sin arrancar cada contenedor a mano?"
resumen: "un docker-compose.yml declara los servicios y sus dependencias; `docker compose up` los levanta todos con una red y volúmenes compartidos."
fecha: 2026-08-22
---

# Cómo usar docker compose para levantar varios servicios

Un `docker-compose.yml` mínimo con tres servicios que dependen entre
sí:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ejemplo
    volumes:
      - datos_db:/var/lib/postgresql/data

  backend:
    build: ./backend
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:ejemplo@db:5432/postgres
    ports:
      - "8000:8000"

  worker:
    build: ./worker
    depends_on:
      - db

volumes:
  datos_db:
```

Comandos básicos:

```bash
docker compose up -d          # levanta todo en segundo plano
docker compose logs -f backend  # sigue los logs de un solo servicio
docker compose down           # para y elimina los contenedores (no los volúmenes)
docker compose down -v        # + elimina también los volúmenes (borra los datos)
```

Puntos que suelen sorprender:

- Dentro de la red interna de compose, cada servicio se referencia por
  su **nombre de servicio** como si fuera un hostname (`db`, no
  `localhost`) — por eso `DATABASE_URL` usa `db` como host.
- `depends_on` solo controla el **orden de arranque** del contenedor,
  no espera a que el servicio esté realmente listo para aceptar
  conexiones (p. ej. Postgres tarda un poco más en aceptar queries que
  en arrancar el proceso) — si el backend falla al conectar la primera
  vez, hace falta un healthcheck o reintentos en el propio backend.
- Los volúmenes con nombre (`datos_db`) sobreviven a `docker compose
  down`; solo desaparecen con `-v` o `docker volume rm` explícito.
