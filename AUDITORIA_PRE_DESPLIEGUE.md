# NormaEdu 2

# Auditoría predespliegue - versión coste cero

## Comprobaciones realizadas

- Sintaxis de `app.py` validada con `python -m py_compile app.py`.
- Eliminada dependencia de Supabase en código y `requirements.txt`.
- Confirmado que la app ya no requiere `SUPABASE_URL` ni `SUPABASE_KEY`.
- Confirmado que el contador `consultas_sesion` no se reinicia al borrar el historial local.
- Confirmado que el nivel educativo ya no se aplica como filtro duro de Qdrant.
- Confirmado que el contexto enviado al LLM se recorta con `MAX_CHARS_CONTEXTO`.
- Confirmado que el máximo de respuesta se limita con `MAX_TOKENS_RESPUESTA`.

## Corrección adicional de auditoría

La primera versión modificada ocultaba errores de Qdrant devolviendo una lista vacía. Eso podía hacer que un problema real de conexión o credenciales pareciera simplemente “no encontré normativa”.

Se ha corregido para que los errores de Qdrant se muestren como error técnico claro.

## Límites que siguen existiendo

- El límite de 10 consultas es por sesión de Streamlit, no por usuario global ni por día.
- No hay persistencia externa porque se ha eliminado Supabase para mantener coste 0 y reducir riesgos RGPD.
- El prompt jurídico no se ha rediseñado todavía; queda para una fase posterior.
- La colección Qdrant sigue teniendo metadatos pobres y bloques mal clasificados; esto se resolverá con `normativa_v2`.
