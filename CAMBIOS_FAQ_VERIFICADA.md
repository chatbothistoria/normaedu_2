# Cambios - FAQ normativa verificada

Fecha: 2026-05-19

## Objetivo

Añadir una capa local de preguntas frecuentes verificadas antes del RAG para:

- responder preguntas factuales frecuentes sin consumir tokens de Cerebras;
- reducir alucinaciones en datos estables;
- mantener coste 0;
- dejar trazabilidad documental de cada respuesta FAQ.

## Archivos añadidos

- `faq_normativa.json`: base de 60 FAQ verificadas.
- `MATRIZ_VERIFICACION_FAQ.md`: matriz de trazabilidad con fuente, página y fragmento de apoyo.

## Funcionamiento

La app intenta primero encontrar una FAQ verificada mediante coincidencia conservadora.

Si hay coincidencia clara:

1. responde desde `faq_normativa.json`;
2. muestra la fuente oficial;
3. no llama a Qdrant;
4. no llama a Cerebras;
5. no incrementa el contador de consultas gratuitas de IA.

Si no hay coincidencia clara, la app continúa con el flujo RAG normal:

Qdrant -> fragmentos -> Cerebras -> validación de citas `[F#]`.

## Criterios de verificación

Cada FAQ incluye:

- pregunta canónica;
- variantes de activación;
- respuesta breve;
- fuente oficial;
- página cuando procede;
- fragmento verificado;
- fecha de verificación;
- riesgo.

No se incluyen respuestas que no tengan soporte documental claro.

## Nota de mantenimiento

La FAQ debe revisarse cuando cambie la normativa o cuando se incorporen nuevas fuentes oficiales.
