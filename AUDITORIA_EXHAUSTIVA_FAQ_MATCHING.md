# Auditoría exhaustiva FAQ matching — NormaEdu 2

Fecha: 2026-05-19

## Objetivo

Revisar la capa de FAQ verificada antes de despliegue y comprobar que las reglas nuevas no introducen falsos positivos peligrosos.

## Hallazgos de la primera auditoría

Se detectaron dos riesgos en la primera versión del matching mejorado:

1. La regla/score de `fp_numero_familias` podía activarse ante preguntas sobre **familias del alumnado**, por ejemplo: “familias de alumnos en FP, cuántas reuniones hay”.
2. La regla de `permiso_hospitalizacion_padre` podía confundirse con frases donde el padre **trabaja en un hospital**, no donde está hospitalizado.

## Hallazgo adicional de la segunda auditoría

Se detectó un riesgo de privacidad: preguntas como “¿Qué hago con un alumno llamado Juan Pérez?” no activaban la FAQ de privacidad y podían pasar al RAG/LLM.

## Correcciones aplicadas

1. Se añadió `_faq_contiene_contexto_familiar_no_profesional()` para distinguir familias profesionales de familias del alumnado.
2. Se endureció la regla de FP para que la FAQ de número de familias solo salte cuando la intención sea claramente “número de familias profesionales”.
3. Se añadió una protección extra en el matcher por score para que `fp_numero_familias` no salte por similitud textual ante preguntas sobre familias de alumnos.
4. Se endureció la regla de hospitalización: ahora exige `hospitalizado`, `hospitalizada`, `hospitalización`, `ingresado`, `ingresada` o `ingreso hospitalario`; ya no basta con que aparezca la palabra “hospital”.
5. Se amplió la regla de Bachillerato para que `Orden EDU/425/2024` active correctamente la FAQ aunque el usuario no escriba explícitamente “Castilla y León”.
6. Se añadió detección de datos potencialmente identificativos: DNI, expedientes, diagnósticos, datos médicos, “alumno llamado…”, “alumno Juan Pérez”, etc.
7. Se añadió una excepción prudente para consultas expresamente anonimizadas o “sin nombres”, siempre que no incluyan datos sensibles.
8. Se extendió la FAQ de permiso de hospitalización a madre/padre como familiar de primer grado.
9. Se normalizó la metadata de `faq_normativa.json`: versión `0.3`, 61 FAQ.

## Pruebas realizadas

Se ejecutaron 30 pruebas:

- 10 preguntas trampa originales.
- 20 pruebas adicionales de estrés para detectar falsos positivos y falsos negativos.

Resultado final:

```text
30/30 PASS
0 FAIL
```

El detalle está en:

- `resultados_auditoria_faq_matching_v4.csv`
- `resultados_auditoria_faq_matching_v4.json`

## Limitaciones

Esta auditoría comprueba la lógica local de FAQ, sintaxis de Python, ausencia de secretos y estructura del paquete. No prueba en vivo Qdrant ni Cerebras porque requiere las claves reales del despliegue.

## Conclusión

La versión auditada es más segura que la anterior. Mantiene las mejoras de cobertura, reduce falsos positivos en familias profesionales y permisos, y añade una protección importante frente a consultas con datos personales identificativos.
