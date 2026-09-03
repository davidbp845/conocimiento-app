---
titulo: "Diferencia entre Dockerfile y docker-compose.yml"
tags: [docker, cli]
categoria: docker
fuente: claude_code
pregunta_origen: "¿el Dockerfile y el docker-compose.yml hacen lo mismo? ¿necesito los dos?"
resumen: "el Dockerfile construye la imagen de un servicio; docker-compose.yml declara cómo se levantan y conectan varios servicios (imágenes) juntos."
fecha: 2026-08-23
---

# Diferencia entre Dockerfile y docker-compose.yml

Resuelven problemas distintos, y casi siempre se usan juntos:

**`Dockerfile`**
- Define **cómo se construye una imagen**: desde qué base parte, qué
  dependencias instala, qué código copia dentro, qué comando arranca.
- Un servicio propio (tu backend, tu worker) casi siempre necesita uno.
- Se construye con `docker build -t mi-imagen .`

**`docker-compose.yml`**
- Define **cómo se levantan y conectan varios contenedores**: qué
  imagen usa cada uno (una que tú construyes con tu `Dockerfile`, o una
  ya publicada como `postgres:16`), en qué red, con qué variables de
  entorno, qué puertos expone, de qué otros servicios depende.
- No sustituye al `Dockerfile` — lo referencia (`build: ./backend`) para
  los servicios que necesitan construirse desde código propio, y usa
  `image: ...` directamente para los que no.

En corto: si solo necesitas **un** contenedor con una imagen ya
publicada (p. ej. una base de datos de prueba), te basta un `docker run`
o unas pocas líneas de `docker-compose.yml` sin `Dockerfile` propio. En
cuanto hay **código tuyo** que empaquetar, hace falta un `Dockerfile`
para esa imagen — y `docker-compose.yml` sigue siendo lo que coordina
ese contenedor con los demás (base de datos, caché, worker...).

## Ver también

- [[como-usar-docker-compose-para-levantar-varios-servicios]]
- [[como-reducir-el-tamano-de-una-imagen-docker]]
