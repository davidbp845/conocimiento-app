# conocimiento_app — motor para archivar conocimiento tipo tutorial/procedimiento

Motor reutilizable para archivar, de forma buscable y clasificada, las
respuestas tipo tutorial/procedimiento que genero (Claude) cuando
explico cómo usar una herramienta, un comando o resolver una tarea
concreta. Cada respuesta queda como una nota Markdown con frontmatter
en `vault_out/`, visualizable y buscable desde un panel Streamlit, y
alcanzable también por Telegram para poder preguntar (y archivar la
respuesta) estés donde estés, mientras el proceso esté corriendo en el
ordenador.

Este repo trae **contenido de ejemplo** en `vault_out/` (notas sobre
git, docker y Streamlit) para que el panel y la CLI tengan algo que
mostrar nada más clonarlo — no una carpeta vacía. Sustitúyelo por tu
propio conocimiento sin problema.

Arquitectura hexagonal (puertos y adaptadores), inspirada en los
proyectos hermanos `orquestador` y `heruka-life`. El dominio (qué es
una nota, cómo se clasifica, cómo se reorganiza el árbol) no sabe nada
de Telegram, de Anthropic ni de Streamlit — esos son adaptadores
intercambiables.

> Estado actual: las siete capas están implementadas y probadas —
> `domain/` (entidades, puertos, casos de uso, excepciones),
> `config/` (schema + loader + `conocimiento.yaml` + `paths.py`),
> `application/` (prompts), `adapters/out/` (`RepositorioNotasFilesystem`,
> `GeneradorRespuestasAnthropic`/`ClasificadorNotasAnthropic`/
> `NormalizadorVaultInAnthropic`, y sus equivalentes `*Mock`),
> `adapters/in_/` (`cli.py` — incluye `normalizar`, la versión
> automatizable de `/normalizar-vault-in`, sin Claude Code de por
> medio — y `telegram_bot.py`) y `main.py` (composition root). 113
> tests en `pytest` (ninguno necesita red, API key ni un bot de
> Telegram real — los adaptadores de salida se prueban mockeando el
> SDK correspondiente, mismo criterio que `orquestador`) y
> `ruff check .` limpio. No probado todavía: una conversación real con
> el bot de Telegram (hace falta un
> `TELEGRAM_BOT_TOKEN` real) ni el panel Streamlit abierto en un
> navegador. `requirements.txt`/`requirements-dev.txt` reflejan las
> dependencias reales ya usadas, no una lista provisional.

## Dos formas de usarlo

1. **Standalone** (clonas solo este repo): usa su propio
   `vault_in/`/`vault_out/`/`.env`, tal cual están aquí — con el
   contenido de ejemplo de `vault_out/` de partida.
2. **Embebido como submódulo git** de otro repo que guarda ahí su vault
   real (privado, con tu propio conocimiento). Ese repo host exporta la
   variable `CONOCIMIENTO_HOME` apuntando a su propia raíz antes de
   lanzar cualquier script de aquí (ver `config/paths.py`); a partir de
   ahí, `.env`, `vault_in/` y `vault_out/` se resuelven contra esa
   ruta en vez de contra la de este repo. Sin `CONOCIMIENTO_HOME`
   definida, todo cae de vuelta al modo standalone (punto 1).

## Estructura

```
domain/           → entidades (Nota), puertos (interfaces) y casos de
                     uso: guardar una nota, clasificarla, reorganizar
                     el árbol de vault_out, buscar. Sin dependencias
                     externas — es lo único que de verdad define "qué
                     es" este proyecto.
application/      → prompts.py: el texto de los prompts (estilo
                     tutorial, reglas de clasificación), separado de
                     domain/use_cases.py (que ya coordina el flujo
                     pregunta → respuesta → nota) y de adapters/out/
                     (que decide cómo llamar al LLM). No hay una
                     capa "orquestador" aparte: con una sola llamada
                     al LLM por caso de uso (sin bucle de tools),
                     domain/use_cases.py ya es esa coordinación.
adapters/in_/     → entradas: bot de Telegram (preguntar desde
                     cualquier sitio, o capturar una conversación
                     entera con /iniciar-/finalizar — ver "Bot de
                     Telegram" más abajo) y CLI (comandos de terminal:
                     guardar, buscar, reorganizar — ver más abajo).
adapters/out/     → salidas: LLM (Anthropic, o un mock para
                     desarrollar sin gastar tokens), y el repositorio
                     de notas que lee/escribe los .md de vault_out.
config/           → configuración declarativa (YAML) + loader: reglas
                     de clasificación, límites del árbol de carpetas
                     (ver "Crecimiento del árbol" más abajo); y
                     paths.py, que resuelve dónde viven .env/vault_in/
                     vault_out (ver "Dos formas de usarlo" arriba) sin
                     depender del directorio de trabajo del proceso.
streamlit_app/    → panel con dos pestañas: Chat (pregunta -> LLM ->
                     nota nueva en vault_out, reusando
                     ResponderYArchivar igual que el bot de Telegram,
                     fuente=streamlit; selector Anthropic/OpenAI por
                     sesión — a diferencia del bot de Telegram y de
                     `reorganizar`, que siguen fijos al proveedor de
                     PROVEEDOR_LLM) y Buscar (visualiza/busca las
                     notas ya archivadas y permite eliminarlas una a
                     una, con confirmación en dos pasos — para quitar
                     duplicados, p. ej. una misma pregunta archivada
                     dos veces). Proyecto hermano ligero: no
                     reimplementa generación ni búsqueda, solo las
                     reusa. La pestaña Chat necesita ANTHROPIC_API_KEY
                     y/o OPENAI_API_KEY según el proveedor elegido (o
                     PROVEEDOR_LLM=mock para probar sin ninguna); la
                     pestaña Buscar no necesita ninguna.
vault_in/         → bandeja de entrada para .md pegados a mano, o
                     volcados por el bot de Telegram (ver "Bot de
                     Telegram" más abajo): sin frontmatter, o con
                     frontmatter incompleto. Dos formas de normalizarla
                     a vault_out/ (plana, categoria: null, igual que
                     ResponderYArchivar): `cli.py normalizar`
                     (automatizable, sin Claude Code de por medio — ver
                     "Comandos básicos") o `/normalizar-vault-in` desde
                     una sesión de Claude Code (más lento, pero más
                     cuidadoso: puede razonar caso a caso). Viene vacía
                     en este repo (ver vault_in/README.md).
vault_out/        → las notas ya redactadas, el conocimiento en sí.
                     Empieza plana; el comando `reorganizar` es el
                     único que crea subcarpetas (ver más abajo). Trae
                     contenido de ejemplo en este repo (ver arriba).
main.py           → composition root: conecta las piezas y arranca el
                     bot de Telegram (el "proceso funcionando en el
                     ordenador").
scripts/          → utilidades de desarrollo (arrancar/parar todo a
                     la vez, verificar entorno...).
tests/            → carpetas numeradas siguiendo el orden de
                     dependencia de la arquitectura (dominio → config
                     → aplicación → adaptadores de salida →
                     adaptadores de entrada), mismo patrón que
                     orquestador/heruka-life.
```

## Formato de una nota (`vault_out/*.md`)

Frontmatter YAML + cuerpo Markdown, mismo estilo que los vaults de
Obsidian de los proyectos hermanos:

```markdown
---
titulo: "Cómo revertir el último commit sin perder los cambios"
tags: [git, cli]
categoria: null          # ruta relativa dentro de vault_out; null hasta que "reorganizar" la asigna
fuente: telegram          # telegram | cli | claude-code | streamlit | manual
pregunta_origen: "¿cómo deshago el último commit pero me quedo con los cambios en el working tree?"
resumen: "git reset --soft HEAD~1 deshace el commit y deja los cambios staged."
fecha: 2026-08-15
---

# Cómo revertir el último commit sin perder los cambios
...
```

`categoria` es lo que decide en qué subcarpeta vive la nota; el resto
del frontmatter (`tags`, `resumen`) alimenta la búsqueda del panel
Streamlit aunque la nota no se haya reorganizado todavía.

## Crecimiento del árbol de `vault_out/`

Reglas que respeta `PlanificarReorganizacion` (`domain/use_cases.py`)
para que el árbol crezca de forma armoniosa:

1. **Una nota vive en exactamente una carpeta.** Nada de que un mismo
   tema encaje en dos ramas a la vez — si una nota duda entre dos
   sitios, es señal de que la taxonomía necesita ajustarse, no de
   duplicar la nota.
2. **No se crea una subcarpeta hasta que hay contenido suficiente que
   la justifique** (umbral configurable en `config/`, por defecto unas
   5 notas afines — `config/conocimiento.yaml` de este repo lo baja a
   2 solo para que el `vault_out/` de ejemplo sea reproducible con
   `reorganizar --aplicar`; un vault real debería mantener el 5).
   Evita ramas con uno o dos archivos.
3. **Se prioriza ampliar/reusar una carpeta existente** sobre crear una
   nueva, si el tema encaja razonablemente.
4. **Profundidad máxima limitada** (por defecto 2 niveles) para que el
   árbol siga siendo hojeable a mano, aunque la búsqueda del panel no
   dependa de ello.
5. El comando corre **en modo simulación por defecto**: muestra el plan
   de movimientos (qué nota iría a qué carpeta) antes de tocar nada;
   hace falta `--aplicar` para ejecutarlo de verdad.

## Puesta en marcha

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Rellena ANTHROPIC_API_KEY (o pon PROVEEDOR_LLM=mock para probar sin
# gastar tokens ni tener API key) y, si quieres el bot, TELEGRAM_BOT_TOKEN
# (créalo hablando con @BotFather) y TELEGRAM_CHAT_ID_PERMITIDO.
```

## Comandos básicos

```bash
# Arrancar el proceso principal: bot de Telegram escuchando preguntas.
# Cada pregunta recibida se responde y la respuesta se guarda como
# nota nueva en vault_out/, plana, a la espera de reorganización.
python main.py

# Guardar a mano una nota ya redactada (p. ej. cuando yo, en una sesión
# de Claude Code, redacto directamente el markdown sin pasar por el
# adaptador LLM) — añade el frontmatter que falte y la deja en vault_out/.
python -m adapters.in_.cli guardar --archivo respuesta.md
cat respuesta.md | python -m adapters.in_.cli guardar --stdin

# Buscar notas por texto y/o tags (lo mismo que usa el panel Streamlit).
python -m adapters.in_.cli buscar "docker compose"
python -m adapters.in_.cli buscar --tag git --tag cli

# Reorganizar vault_out/ en subcarpetas siguiendo las reglas de arriba.
# Por defecto solo muestra el plan (dry-run).
python -m adapters.in_.cli reorganizar
python -m adapters.in_.cli reorganizar --aplicar

# Normalizar vault_in/: cada .md pendiente -> una o varias notas en
# vault_out/ (borra el original de vault_in/ solo con --aplicar). Es
# lo que corre el timer systemd cada 10 min en producción (ver
# despliegue), sin depender de Claude Code.
python -m adapters.in_.cli normalizar
python -m adapters.in_.cli normalizar --aplicar

# Panel de visualización y búsqueda.
streamlit run streamlit_app/app.py

# Tests y lint.
pip install -r requirements-dev.txt
pytest
pytest tests/01_domain   # una sola capa
ruff check .
```

## Bot de Telegram

Dos formas de usarlo (`adapters/in_/telegram_bot.py`), sin mezclarse
entre sí:

- **Pregunta suelta**: cualquier mensaje de texto normal se trata como
  pregunta → el LLM genera una respuesta tipo tutorial → se archiva
  directa en `vault_out/` (`fuente: telegram`), igual que siempre.
- **Conversación capturada**: `/iniciar` empieza a acumular en memoria
  (sin llamar al LLM, sin responder más que un `✓` por mensaje) todo lo
  que escribas a continuación; `/finalizar` vuelca esos mensajes,
  en orden y separados por párrafo, como un único `.md` nuevo en
  `vault_in/` (`telegram-AAAA-MM-DD-HHMMSS-ffffff.md`, sin
  frontmatter) — pendiente de que lo recoja `/normalizar-vault-in`.
  Útil para pegar/dictar por partes una conversación larga de otra IA,
  o varias ideas sueltas, sin que cada mensaje individual dispare una
  respuesta y una nota aparte.

`/iniciar` dos veces seguidas no reinicia ni pierde lo ya acumulado; ni
esa conversación en curso ni sus mensajes se persisten a disco hasta
`/finalizar` — si el proceso se reinicia a media captura, se pierde a
propósito (mejor eso que volcar a `vault_in/` una conversación a
medias sin que nadie lo haya pedido).

## Cómo sustituir un adaptador

Ejemplo: pasar el repositorio de notas de ficheros locales a otra
cosa (p. ej. sincronizado con un Obsidian vault real, o una base de
datos).

1. Crea `adapters/out/repositorio_notas_<x>.py` implementando el mismo
   puerto de `domain/ports.py` (`RepositorioNotas`).
2. En `main.py`, cambia la instanciación en `construir_sistema()`.
3. `domain/` y `application/` no cambian.

## Comandos de Claude Code (`.claude/commands/`)

- `/guardar-respuesta [título]` — archiva la última respuesta
  sustancial de la conversación como nota nueva en `vault_out/`.
  Sigue siendo útil con los adaptadores ya implementados: es más
  rápido que redactar el fichero y llamar a `cli.py guardar` a mano
  desde una sesión de Claude Code.
- `/buscar-notas [texto o #tag]` — busca en las notas ya archivadas.
- `/reorganizar-vault [--aplicar]` — calcula (y, con `--aplicar`,
  ejecuta) el plan de reorganización en subcarpetas. Hace lo mismo que
  `cli.py reorganizar` con un `ClasificadorNotas` real; útil sobre
  todo si no hay `ANTHROPIC_API_KEY` a mano en ese momento.
- `/normalizar-vault-in [--aplicar]` — detecta los .md de vault_in/ con
  frontmatter ausente o incompleto, infiere lo que falta (título —
  optimizado, no copiado literal; resumen; tags; una `pregunta_origen`
  razonable cuando el cuerpo es la respuesta directa de una IA sin
  pregunta escrita — nunca `categoria`) y los traslada ya normalizados
  a vault_out/. También detecta cuerpos aplanados (texto pegado desde
  una conversación de IA a un canal de Telegram, sin saltos de línea y
  con los `/comando` convertidos en enlaces `tg://bot_command`), los
  reformatea — párrafos, listas, diagramas ASCII — y fusiona los
  fragmentos en los que la IA repite una respuesta anterior ya
  retocada con un dato nuevo del usuario, antes de archivarlos.
  Dry-run por defecto, igual que `/reorganizar-vault`.
- `/siguiente-pieza [pieza]` — continúa implementando/refinando *este
  motor* capa a capa, siguiendo el orden y el estilo ya establecidos.
  Comando de desarrollo del propio `conocimiento_app`, no de uso diario
  del vault — no lo expongas si embebes este repo como submódulo de
  otro pensado solo para archivar conocimiento.
- `/ayuda` — lista estos comandos desde su frontmatter.

## Pendiente de decidir

- Probar el bot de Telegram con un `TELEGRAM_BOT_TOKEN` real (hasta
  ahora solo probado con el SDK mockeado) y el panel Streamlit abierto
  en un navegador.
- Si el clasificador de tags/carpeta debería poder usar un prompt/rol
  distinto al de generación en vez del mismo modelo con dos prompts
  separados (ahora mismo: mismo modelo, `application/prompts.py` ya
  separa los dos textos).

## Licencia

MIT — ver [LICENSE](LICENSE).
