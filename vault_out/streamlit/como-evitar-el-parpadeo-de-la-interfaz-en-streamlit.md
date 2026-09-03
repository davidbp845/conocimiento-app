---
titulo: "Cómo evitar el parpadeo de la interfaz en Streamlit"
tags: [streamlit, python]
categoria: streamlit
fuente: claude_code
pregunta_origen: "al cargar mi app de Streamlit, la cabecera aparece un instante y luego desaparece/se mueve — ¿cómo lo evito?"
resumen: "el parpadeo suele venir de CSS inyectada vía st.markdown(unsafe_allow_html=True): llega como delta por WebSocket después del primer pintado; los ajustes de .streamlit/config.toml se aplican antes del primer render y no parpadean."
fecha: 2026-08-29
---

# Cómo evitar el parpadeo de la interfaz en Streamlit

Un parpadeo típico: la cabecera (o cualquier otro elemento) aparece un
instante con su aspecto por defecto y, justo después, cambia — se
oculta, cambia de tamaño, se mueve. La causa habitual no es lentitud,
es **cuándo llega el cambio**:

- `st.markdown("<style>...</style>", unsafe_allow_html=True)` se
  ejecuta como un elemento más del script, en el punto donde aparece —
  Streamlit ya ha pintado el layout antes de que ese `<style>` llegue
  por WebSocket, así que el navegador muestra primero el estado sin él
  y un instante después el estado con él. Eso es el parpadeo, no un
  problema de rendimiento.
- Mover el `st.markdown` a otro sitio del script no lo arregla —el
  problema es que sea un delta que llega *después* del primer pintado,
  no su posición.

**La alternativa que sí evita el parpadeo:** todo lo que se pueda
configurar vía `.streamlit/config.toml` se aplica *antes* del primer
render, así que el navegador nunca llega a mostrar el estado
"sin aplicar":

```toml
[client]
toolbarMode = "minimal"   # quita el botón "Deploy" y el menú de la cabecera
```

Y para estado que sí depende de datos en tiempo de ejecución (no un
ajuste fijo de config), mejor un widget nativo colocado en su sitio
normal del flujo del documento (un `st.form`, un `st.container`) que
`unsafe_allow_html` — un widget nativo se monta ya en su posición
final desde el primer render, sin depender de JS/CSS que se aplique
después.

## Ver también

- [[guia-rapida-de-streamlit-session-state]]
