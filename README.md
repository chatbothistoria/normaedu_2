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

## Modo diagnóstico

La barra lateral incluye `🔎 Modo diagnóstico`. Permite ver:

- si la respuesta viene de FAQ o RAG/IA;
- qué FAQ se activó y con qué puntuación;
- si se ha usado Qdrant;
- si se ha usado IA;
- fragmentos recuperados y puntuaciones;
- citas detectadas e inválidas;
- errores temporales de IA y reintentos si los hay.

No guarda datos personales ni añade coste.

## v054

Esta versión mantiene oculto el proveedor de IA en los mensajes de usuario y archivos públicos, usa Secrets genéricos (`IA_API_KEY`, `IA_API_URL`, `IA_MODEL`) y añade un reintento automático suave cuando la IA devuelve un límite temporal. Si el reintento falla, la app muestra un mensaje genérico de límite temporal y las FAQ siguen funcionando sin consumir tokens de IA.
