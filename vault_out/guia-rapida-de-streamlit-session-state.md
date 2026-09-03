---
titulo: "Guía rápida de st.session_state en Streamlit"
tags: [streamlit, python]
categoria: null
fuente: claude_code
pregunta_origen: "en streamlit cada interacción relanza el script entero — ¿cómo guardo un valor entre una interacción y la siguiente?"
resumen: "st.session_state es un dict que sobrevive a los reruns dentro de la misma sesión de navegador; inicializa cada clave con `if clave not in st.session_state` antes de leerla."
fecha: 2026-08-28
---

# Guía rápida de st.session_state en Streamlit

Streamlit vuelve a ejecutar el script completo de arriba a abajo en
cada interacción (un clic, un `text_input` que cambia...). Cualquier
variable normal de Python se pierde entre una ejecución y la
siguiente — para que algo persista dentro de la misma sesión de
navegador hace falta `st.session_state`.

```python
if "contador" not in st.session_state:
    st.session_state.contador = 0

if st.button("Sumar"):
    st.session_state.contador += 1

st.write(st.session_state.contador)
```

Reglas prácticas:

- **Inicializa siempre con el patrón `if clave not in st.session_state`**
  antes de leer o incrementar — si no, el primer rerun (antes de que
  exista la clave) lanza `KeyError` o pisa el valor cada vez.
- Un widget con `key="algo"` escribe automáticamente su valor en
  `st.session_state["algo"]` — no hace falta sincronizarlo a mano, pero
  cuidado con inicializar esa misma clave manualmente después de crear
  el widget: Streamlit lanza `StreamlitAPIException` si intentas
  asignarla tú una vez que el widget ya la controla.
- `st.session_state` es **por sesión de navegador**, no compartido
  entre usuarios ni entre pestañas con sesiones distintas — para
  estado compartido entre varias sesiones hace falta algo externo
  (fichero, base de datos, `st.cache_resource` para un recurso
  reusado como una conexión, no como datos mutables por usuario).
- Se resetea si se recarga la página desde cero (F5) — solo sobrevive
  a los reruns que Streamlit dispara internamente por interacción.
