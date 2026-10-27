# Clarify

## Qué es el paso clarify en Spec Kit

Es la fase que va entre specify y plan. La spec recién escrita casi siempre deja decisiones abiertas que parecen menores, pero cambian cómo se implementa o cómo se prueba. Clarify las busca, te las pregunta y escribe las respuestas dentro de la misma spec. Así el plan arranca sobre decisiones ya tomadas y no sobre suposiciones.

Se puede saltar, pero el riesgo de retrabajo sube. Si el plan supone algo que la spec no dijo, lo descubres en implement, que es el momento más caro.

## Qué hace el skill /speckit-clarify

1. Lee la spec de la feature activa y la constitución.
2. Revisa la spec contra una taxonomía de categorías: alcance, modelo de datos, flujos de error, atributos no funcionales (rendimiento, confiabilidad, seguridad), casos borde, restricciones y terminología. Marca cada una como Clear, Partial o Missing.
3. Arma una cola interna de preguntas y la prioriza por impacto × incertidumbre. **Máximo 5 preguntas** por sesión.
4. Pregunta **una a la vez**. Cada pregunta trae una opción recomendada con su razón y una tabla de opciones. Respondes con la letra, con "yes" para aceptar la recomendada, o con una respuesta corta propia.
5. Después de cada respuesta actualiza la spec en dos lugares:
   - Agrega una línea `- Q: ... → A: ...` en `## Clarifications > ### Session <fecha>` (el registro).
   - Aplica la decisión en la sección que corresponde: requisitos funcionales, casos borde, entidades, criterios de éxito o supuestos.
6. Si la respuesta contradice algo que ya estaba escrito, **reemplaza** el texto viejo en lugar de duplicarlo. La spec no debe quedar con dos versiones de la misma regla.
7. Vuelve a validar el checklist de calidad (`checklists/requirements.md`) contra la spec actualizada.

Ojo: no pregunta por el stack técnico (qué base de datos, qué framework). Pregunta por **comportamiento**. "¿Las cuentas sobreviven a un reinicio?" es una pregunta de clarify. "¿Usamos SQLite o Postgres?" es una pregunta de plan.

## Lo que hicimos en el ejercicio (feature 001-cuentas-bancarias)

Sesión 2026-10-13, 5 preguntas respondidas:

| Pregunta | Decisión | Dónde quedó en la spec |
|---|---|---|
| ¿Las cuentas sobreviven a un reinicio? | Sí, persistencia durable | FR-006, SC-001 |
| Si hay varios campos inválidos, ¿el error los nombra todos? | Sí, todos | FR-003a nuevo, escenario 8, SC-002 |
| ¿Se recortan los espacios del titular? | Sí, antes de validar y guardar; el límite de 100 se mide sobre el valor recortado | FR-002a nuevo, caso borde, entidad Cuenta, supuestos |
| ¿Hay saldo inicial máximo? | Sí, 1.000.000,00 inclusive | FR-003, caso borde, entidad Cuenta |
| ¿Se acepta el saldo como texto ("1000")? | No, solo valor numérico | FR-003, caso borde (reemplazó el anterior) |

Al final no quedó ningún `NEEDS CLARIFICATION` y el checklist quedó completo.

## Lo que aprendí

- **Una respuesta toca varias secciones.** La decisión del titular recortado cambió un FR, un caso borde, la entidad y un supuesto. Si solo la anotas en Clarifications, el resto de la spec queda desalineado.
- **Requisitos nuevos con sufijo (FR-002a, FR-003a).** Así no se renumeran los existentes y no se rompen las referencias que ya los citaban.
- **Los límites se escriben con el valor exacto.** "1.000.000,00 se acepta, 1.000.000,01 se rechaza" se convierte directamente en dos pruebas de integración. Encaja con la constitución, que pide pruebas antes de implementar.
- **Las preguntas que parecen menores cambian el diseño.** "Listar todos los errores" obliga a validar todos los campos antes de responder, sin cortar en el primero. "Durable" descarta guardar en memoria. Ninguna de las dos se ve en la spec original.
- **El registro Q → A deja la decisión trazable.** Dentro de unos meses se puede saber por qué el saldo no acepta texto y en qué sesión se decidió.

## Después de clarify

1. Hacer commit de la spec actualizada (`spec(001): integrate clarify session 2026-10-13`).
2. Opcional: `/speckit-report` para ver en qué fase va cada feature.
3. Siguiente fase: `/speckit-plan`.
