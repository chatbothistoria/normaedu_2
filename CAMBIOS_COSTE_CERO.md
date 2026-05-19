# NormaEdu 2

# Cambios aplicados para modo coste 0

Cambios incluidos en esta versión:

1. Supabase eliminado/desactivado
   - Eliminado `from supabase import create_client`.
   - Eliminadas las claves `SUPABASE_URL` y `SUPABASE_KEY` como requisito.
   - `guardar_log()` y `guardar_feedback()` quedan como funciones no persistentes.
   - Ya no se guardan preguntas ni respuestas en una base de datos externa.

2. Límites duros de uso
   - `MAX_PREGUNTAS_SESION = 10`.
   - `MAX_TOKENS_RESPUESTA = 900`.
   - `MAX_CHARS_CONTEXTO = 18000`.
   - `MATCH_COUNT = 8` fragmentos finales.
   - `MATCH_COUNT_RETRIEVAL = 40` candidatos iniciales.
   - El contador de uso no se reinicia al borrar el historial de chat.

3. Nivel educativo como preferencia, no como filtro excluyente
   - Qdrant ya no filtra de forma dura por `bloque`.
   - Primero recupera candidatos de toda la colección.
   - Luego reordena localmente dando un bonus pequeño si el bloque coincide.
   - Esto evita perder normativa relevante mientras se corrigen los metadatos de Qdrant.

4. Búsqueda textual remota desactivada
   - La colección actual no tiene indexado `contenido` para búsqueda textual.
   - La parte keyword se hace localmente sobre los candidatos vectoriales.
   - No se añade ningún servicio externo ni dependencia de pago.

5. Requirements ajustado
   - Eliminado `supabase` de `requirements.txt`.

Pendiente para siguiente fase:
- Cambiar el prompt para que no use conocimiento jurídico externo.
- Validar citas `[F1]`, `[F2]`.
- Reindexar Qdrant como `normativa_v2` con metadatos jurídicos mejores.
