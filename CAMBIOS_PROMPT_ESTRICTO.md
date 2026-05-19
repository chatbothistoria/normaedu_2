# NormaEdu 2 - Cambio de prompt jurídico estricto

Fecha: 2026-05-19

## Objetivo

Reducir alucinaciones jurídicas y evitar que el modelo complete respuestas con conocimiento propio cuando los fragmentos recuperados no son suficientes.

## Cambios realizados

1. **Prompt jurídico estricto**
   - El modelo debe responder solo con los fragmentos proporcionados.
   - Se elimina la instrucción de completar con conocimiento jurídico general.
   - Si falta base documental, debe decir que no hay información suficiente.

2. **Citas obligatorias por fragmento**
   - Los fragmentos se identifican como `[F1]`, `[F2]`, `[F3]`, etc.
   - Las afirmaciones normativas deben citar esos identificadores.
   - Las fuentes mostradas al usuario también incorporan esos identificadores.

3. **Validación básica de citas**
   - La app comprueba que las citas generadas existan en el contexto enviado.
   - Si el modelo cita un fragmento inexistente, la respuesta se bloquea y se muestra una respuesta segura.
   - Si el modelo no incluye citas `[F#]`, se muestra una advertencia de cautela.

4. **Sin arrastre de historial al LLM**
   - Cada consulta se responde solo con la pregunta actual y los fragmentos recuperados.
   - El historial sigue apareciendo en pantalla y en PDF, pero no se usa como contexto para generar nuevas respuestas.

5. **Mejora menor de recuperación léxica**
   - Se dejan de considerar como stopwords términos jurídicos/educativos como `docente`, `alumno` o `derechos`, porque pueden ser importantes para recuperar documentos relevantes.

## Sin coste adicional

No se han añadido APIs, bases de datos, modelos externos ni dependencias nuevas. El cambio mantiene la arquitectura de coste 0:

- Streamlit
- Qdrant free tier
- Cerebras free tier
- reranking local en Python
- sin Supabase
