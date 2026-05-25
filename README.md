# NormaEdu 2

App Streamlit de consulta de normativa educativa con FAQ verificadas, RAG con Qdrant y una capa de IA configurada mediante Secrets. La versión pública no muestra el proveedor de IA a los usuarios.

## Archivos principales

- `app.py`: aplicación principal.
- `requirements.txt`: dependencias.
- `faq_normativa.json`: base local de FAQ verificadas.
- `MATRIZ_VERIFICACION_FAQ.md`: trazabilidad de las FAQ.
- `enlaces.csv`: correspondencia entre documentos y enlaces oficiales.
- `.streamlit/secrets.toml.example`: plantilla segura de configuración.

## Configuración de Secrets en Streamlit Cloud

Configura estos valores en **Manage app → Settings → Secrets**:

```toml
IA_API_KEY = "pega_aqui_tu_clave_de_ia"
IA_API_URL = "https://endpoint-del-proveedor/v1/chat/completions"
IA_MODEL = "nombre-del-modelo"
QDRANT_URL = "https://tu-cluster.cloud.qdrant.io"
QDRANT_API_KEY = "pega_aqui_tu_clave_de_qdrant"

# Opcional: solo para administradores. Permite activar diagnóstico accediendo a ?admin.
ADMIN_DIAGNOSTIC_KEY = "elige_una_clave_larga_para_admin"
```

No subas nunca claves reales a GitHub. El archivo `.streamlit/secrets.toml.example` es solo una plantilla.

## Control de coste 0

- Las FAQ verificadas responden sin usar Qdrant ni IA.
- Las consultas RAG usan Qdrant y la IA solo cuando no hay FAQ aplicable.
- Existe un límite duro de consultas IA por sesión.
- Si la IA devuelve un límite temporal, la app hace un reintento automático suave y no lo presenta como límite diario definitivo.

## Control de fiabilidad jurídica

- Prompt jurídico estricto: la respuesta debe basarse en fragmentos recuperados.
- Citas obligatorias por fragmento `[F1]`, `[F2]`, etc.
- Si la IA cita fragmentos inexistentes, la respuesta se bloquea.
- Si no hay base suficiente en los fragmentos, la app debe responder de forma prudente.

## FAQ normativa verificada

La app incluye `faq_normativa.json` con 130 FAQ verificadas. Esta capa se consulta antes del RAG para ahorrar tokens y reducir errores en preguntas frecuentes.

## Modo diagnóstico protegido

El modo diagnóstico ya no es visible para usuarios normales. Para activarlo:

1. Añade `ADMIN_DIAGNOSTIC_KEY` en los Secrets de Streamlit.
2. Abre la app añadiendo `?admin` al final de la URL, por ejemplo `https://tu-app.streamlit.app/?admin`.
3. Introduce la clave de administrador en la barra lateral.
4. Activa `🔎 Modo diagnóstico`.

Permite ver:

- si la respuesta viene de FAQ o RAG/IA;
- qué FAQ se activó y con qué puntuación;
- si se ha usado Qdrant;
- si se ha usado IA;
- fragmentos recuperados y puntuaciones;
- citas detectadas e inválidas;
- errores temporales de IA y reintentos si los hay.

No guarda datos personales ni añade coste.

## v056

Esta versión mantiene los cambios de v055 y cambia el acceso de administrador: el modo diagnóstico se activa entrando en la ruta `?admin`, por ejemplo `https://tu-app.streamlit.app/?admin`, y usando la clave definida en `ADMIN_DIAGNOSTIC_KEY`. Los usuarios normales no ven el botón de diagnóstico.


## Acceso diagnóstico privado

El modo diagnóstico no se muestra a los usuarios normales.

Para activarlo:

1. Añade en Streamlit Secrets:

```toml
ADMIN_DIAGNOSTIC_KEY = "elige_una_clave_larga_y_privada"
```

2. Entra en:

```text
https://tu-app.streamlit.app/?admin
```

3. Introduce la clave en la barra lateral.

No se usa `pages/admin.py`, para evitar que Streamlit muestre opciones `app/admin` en el menú lateral.


## v060 - Ajuste de FAQ de Primaria

La FAQ `primaria_no_promocion_plan_refuerzo` se ha reforzado para cubrir formulaciones como:

```text
En Primaria, si un alumno no promociona, ¿debe tener algún plan específico?
```

No se ha duplicado la FAQ porque ya existía una respuesta verificada sobre el plan específico de refuerzo tras no promocionar en Primaria.


## v061 - Repetición en Primaria y corrección del campo de pregunta

Cambios mínimos:
- La pregunta «¿En qué cursos de Primaria puede decidirse la repetición?» activa ahora la FAQ `primaria_repetir_cuando_condiciones_cyl`.
- Se corrige un desfase visual del cuadro de pregunta: la app podía mostrar la pregunta anterior mientras respondía a la nueva.
- No se modifican Qdrant, IA, prompt, admin, privacidad ni límites.


## v062 - Primer paquete de FAQ básicas

Añade un paquete de FAQ básicas tras auditar 120 preguntas frecuentes. Incluye cobertura de:
- áreas/asignaturas de Primaria;
- Religión, alternativa y Valores Cívicos y Éticos;
- calificaciones y evaluación en Primaria;
- materias y estructura básica de ESO;
- materias, modalidades y promoción básica en Bachillerato;
- conceptos básicos de FP;
- formación en empresa, régimen general/intensivo y norma estatal de FP;
- uso de fuentes oficiales.

También refuerza variantes de FAQ ya existentes sobre convivencia, permisos, privacidad y evaluación objetiva.


## v064 - Robustez coloquial

Cambios mínimos:
- Refuerza variantes coloquiales reales detectadas en pruebas de usuario.
- Añade una FAQ defensiva: trabajar en un hospital no genera por sí solo derecho a permiso.
- Corrige activación de FAQ para ESO con suspensos, Bachillerato con suspensas, FP general/intensiva, título de Técnico, grado medio, fallecimiento de padre/madre y alumno que no deja dar clase.
- No modifica Qdrant, IA, prompt, admin oculto, privacidad ni límites.


## v064b - Corrección preventiva de despliegue

Mantiene los cambios de v064 y añade:
- versión unificada en diagnósticos;
- eliminación de una modificación potencialmente conflictiva de `pregunta_input_widget` en `st.session_state`.

No cambia FAQ, IA, Qdrant, prompt, admin, límites ni privacidad.

## v065 - Corrección quirúrgica de variantes

- Añade FAQ defensiva `fp_ciclos_por_familia_no_estable`.
- Refuerza variantes cortas/coloquiales prioritarias.
- No modifica IA, Qdrant, prompt, admin oculto, privacidad, límites ni reintentos.


## v066 - Trazabilidad jurídica de fuentes

- Refuerza fuentes de FAQ prioritarias con norma exacta, artículo/apartado y fragmento oficial.
- Mejora trazabilidad en FP, Bachillerato, permisos, convivencia, Primaria, Infantil y privacidad.
- No modifica la lógica de matching, Qdrant, IA, admin oculto, límites, reintentos ni interfaz.


## v067 - Filtro de dominio antes de RAG

Cambios:
- Añade un filtro conservador antes de Qdrant/RAG para preguntas claramente fuera del ámbito educativo/docente.
- Evita que consultas de derecho privado, mercantil o contractual general recuperen normativa irrelevante.
- No modifica FAQ, Qdrant, IA, prompt, admin oculto, privacidad, límites ni reintentos.
- Las preguntas bloqueadas no consumen Qdrant ni IA.


## v068b - Rate limit IA corregido

Corrección sobre v068:
- Se mantiene v067 estable como base.
- Se refuerza `_post_ia_con_reintento`.
- Ante límite/servicio temporal IA: hasta 3 intentos totales.
- Esperas progresivas: 20s y 40s.
- Se registra `reintento_espera_segundos` en el diagnóstico técnico.
- No cambia FAQ, Qdrant, prompt, filtro de dominio, admin, privacidad ni interfaz.


## v069 - Filtro de dominio y variantes sintéticas

Cambios:
- Amplía el filtro de dominio con supuestos fuera del ámbito educativo detectados en auditoría sintética.
- Añade variantes FAQ prioritarias para reducir derivaciones innecesarias a RAG.
- Añade reglas de intención muy acotadas para evitar falsos positivos de matching en Bachillerato y FP.
- No modifica Qdrant, IA, prompt jurídico, admin oculto, privacidad, interfaz ni número de FAQ.


## v070 - Respuestas prudentes contextuales

Cambios:
- Añade orientación práctica cuando la respuesta RAG/IA ya reconoce que no hay información suficiente.
- Se aplica solo a preguntas actuales, locales, de centro o individualizadas.
- No modifica FAQ, Qdrant, prompt, filtro de dominio, rate limit, privacidad ni interfaz general.
- Objetivo: evitar respuestas secas y orientar a fuente oficial, centro, Dirección Provincial o catálogo actualizado.


## v070b - Corrección de prioridad en respuestas prudentes contextuales

Cambios:
- Ajusta el orden de las reglas de orientación práctica.
- Horario, transporte, comedor, plazas, libros, optativas, profesorado y convenios tienen prioridad sobre reglas generales de FP/centro.
- No modifica FAQ, Qdrant, prompt, filtro de dominio, rate limit, privacidad ni interfaz general.


## v071 - Trazabilidad compacta del historial

Cambios:
- Añade trazabilidad compacta al historial en pantalla y a la exportación PDF.
- Registra ruta usada: FAQ, FILTRO_DOMINIO, RAG_IA, RAG_IA_PRUDENTE o RAG_IA_CITAS_BLOQUEADAS.
- Registra si se consultó Qdrant, si se consumió IA, FAQ activada y orientación prudente contextual.
- No modifica FAQ, Qdrant, IA, prompt, filtro de dominio, rate limit ni respuestas.


## v071b - Corrección de trazabilidad de orientación contextual

Cambios:
- Corrige la trazabilidad cuando la propia IA ya genera una sección de orientación práctica contextual.
- En esos casos, la ruta pasa a reflejar `RAG_IA_PRUDENTE`.
- No modifica la respuesta mostrada, FAQ, Qdrant, prompt, filtro de dominio, rate limit ni privacidad.
