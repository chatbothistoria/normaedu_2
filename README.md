# NormaEdu 2

App Streamlit de consulta de normativa educativa con Qdrant y Cerebras, configurada para mantener coste 0 con límites duros de uso.

## Archivos principales

- `app.py`: aplicación principal.
- `requirements.txt`: dependencias sin Supabase.
- `enlaces.csv`: correspondencia entre documentos y enlaces oficiales.
- `CAMBIOS_COSTE_CERO.md`: resumen de cambios aplicados.
- `AUDITORIA_PRE_DESPLIEGUE.md`: revisión previa al despliegue.


## Configuración de Secrets en Streamlit Cloud

La app necesita estas tres claves configuradas en **Manage app → Settings → Secrets**:

```toml
CEREBRAS_API_KEY = "pega_aqui_tu_clave_de_cerebras"
QDRANT_URL = "https://tu-cluster.cloud.qdrant.io"
QDRANT_API_KEY = "pega_aqui_tu_clave_de_qdrant"
```

No subas nunca claves reales a GitHub. El archivo `.streamlit/secrets.toml.example` es solo una plantilla segura.

Si falta alguna clave, la app ya no se caerá con un `KeyError`: mostrará una pantalla de configuración indicando qué secreto falta.

## Control de fiabilidad jurídica

Esta versión usa un prompt jurídico estricto: la respuesta debe basarse solo en los fragmentos recuperados de Qdrant y citar dichos fragmentos como `[F1]`, `[F2]`, etc.

Si la respuesta generada cita fragmentos inexistentes, la app la bloquea. Si no incluye citas por fragmento, la app muestra una advertencia de cautela.


## FAQ normativa verificada

Esta versión incorpora una capa local `faq_normativa.json` que responde preguntas frecuentes verificadas antes de llamar a Qdrant/Cerebras.

- No consume tokens de Cerebras.
- No incrementa el contador de 10 consultas de IA.
- Solo debe activarse ante coincidencias claras o reglas de intención conservadoras.
- Las preguntas no cubiertas por FAQ pasan al RAG normal con prompt jurídico estricto.

La auditoría de matching está documentada en `AUDITORIA_EXHAUSTIVA_FAQ_MATCHING.md` y los resultados de la última batería están en `resultados_auditoria_faq_matching_v4.csv/json`.


## Estado FAQ v0.4

La base local contiene 110 FAQ verificadas. Las FAQ se consultan antes del RAG para ahorrar tokens y reducir alucinaciones en preguntas frecuentes.
