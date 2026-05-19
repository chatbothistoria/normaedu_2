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
