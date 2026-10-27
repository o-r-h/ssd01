---
name: speckit-a-harness
description: >-
  Abre un ticket del harness a partir de una feature de spec-kit con tasks.md
  terminado: traduce tasks.md a plan.json y plan.md en lugar de usar
  task-planner, y verifica la traducción antes de abrir cualquier fase. Usar
  con /ticket-abrir-sdd <carpeta de la feature>.
---

# Apertura de ticket desde spec-kit

`CLI` = `python "$HOME/.claude/hooks/cli.py"`. **Todo cambio de estado pasa por el CLI.**

spec-kit ya decidió el qué y el cómo: spec aclarada, decisiones técnicas con su porqué,
contrato y tareas trazables. Este skill **traduce** ese trabajo al contrato del harness.
No vuelve a planificar. Sigue "Al abrir un ticket" de la skill `ticket-loop` con tres
cambios: el requerimiento sale de la feature (paso 1), el id no lleva prefijo `ISR-`
(paso 3) y task-planner se reemplaza por la traducción de `tasks.md` (paso 5).

## Pasos

0. `CLI hallazgos-pendientes`. Si hay hallazgos pendientes de fases anteriores,
   muéstralos antes de seguir y deja claro que **no bloquean**.
1. Verifica que la carpeta de la feature tenga `spec.md`, `plan.md` y `tasks.md`. Si
   falta `tasks.md`, detente y pide correr `/speckit-tasks` con el argumento de
   trazabilidad: *"cada tarea cita entre paréntesis los FR, las decisiones de research
   (R#) y las rutas del contrato que implementa"*.
2. Pregunta **una sola vez**: id de ticket, número de ticket, nombre del desarrollador
   y fecha (`DD-MM-YYYY`). No los inventes ni los deduzcas del sistema. El CLI no valida
   el formato del id: en un ejercicio puede ser, p. ej., `EJ-123`.
3. Escribe `.harness/tickets/<id>/ticket.md`: el nombre de la feature, un resumen de
   dos o tres líneas y enlaces a `spec.md`, `plan.md` y `tasks.md`. **No copies su
   contenido.**
4. `CLI open-ticket --ticket-id <id> --nroticket <nro> --desarrollador "<NOMBRE>" --fecha <DD-MM-YYYY> --perfil ssd01`
5. **Traduce `tasks.md`** a `.harness/tickets/<id>/plan.json` y
   `.harness/tickets/<id>/plan.md` con la tabla de abajo. Lee `.claude/rules.json` antes
   de escribir `checks_deterministas`. Si existe `.claude/biblioteca/INDEX.md`, léelo:
   cada lección de `## Aprobadas` cuya señal coincida con una fase se agrega a sus
   `anclajes` como `{"ref": ".claude/biblioteca/entradas/<archivo>.md", "confianza": "por_confirmar"}`.
   Las de `## Rechazadas` no se usan.
6. Verifica, en este orden, y corrige y repite hasta que ambos pasen:
   - `python .claude/skills/speckit-a-harness/verificar_traduccion.py <carpeta> .harness/tickets/<id>/plan.json`
   - `CLI validate --contrato plan --archivo .harness/tickets/<id>/plan.json`

   **No se abre ninguna fase con un plan inválido.** Si el verificador falla por la forma
   de `tasks.md` (encabezados que no reconoce), corrige `tasks.md`, no el verificador.
7. Muestra `plan.md` y termina. Desde aquí se usa `/fase fase_1` de producción.

## Tabla de traducción (fase de `tasks.md` → fase de `plan.json`)

Una fase de `plan.json` por cada fase de `tasks.md` (Setup, Foundational, una por
historia de usuario, Polish), en el mismo orden. Nunca se parte ni se junta una fase.

| Campo | Origen |
|---|---|
| `id` | `fase_N`, en el orden de las fases de `tasks.md` |
| `titulo` | El título de la fase en `tasks.md` |
| `pasos` | Una línea por tarea, **empezando por su id** (`T012 …`) y con la ruta de archivo que nombra, en el orden de `tasks.md`. Al final, el paso fijo: `ESCRIBE intento_N/resultado.md con la evidencia, incluida la corrida en rojo si la fase tiene pruebas` |
| `criterio_exito` | Fase de historia: el **Independent Test** y los **Acceptance Scenarios** de esa historia en `spec.md`, **literales**, más el Checkpoint de `tasks.md`. Setup, Foundational y Polish: el Checkpoint y el propósito de la fase, redactado como algo que un humano puede comprobar ("la solución compila", "la API no arranca sin `Auth:ApiKey`"). **Toda fase con tareas de prueba** suma la frase fija de abajo |
| `anclajes` | Cada FR, decisión de research (`R1`…), sección de `data-model.md` o ruta del contrato que citan las tareas de la fase, como `{"ref": "specs/<feature>/spec.md#FR-003", "confianza": "verificado"}` (`research.md#R2`, `data-model.md#<encabezado>`, `contracts/openapi.yaml#/paths/~1recurso`). Son documentos revisados por el humano en clarify y plan. Más las lecciones de la biblioteca (`por_confirmar`) |
| `checks_deterministas` | `["dotnet_build", "constitucion"]` |
| `herramientas_permitidas` | `["read", "edit", "bash"]` (bash para `dotnet`) |
| `depende_de` | Lo que declara la sección "Dependencies & Execution Order" de `tasks.md` |
| `prueba_manual` | `requerida: true` en **todas** las fases. `url`: la URL local de la API. `datos`: cómo configurar la credencial y levantar la API, según `quickstart.md`. El guion paso a paso lo deriva el orquestador de `criterio_exito`; por eso los escenarios van literales en el criterio |
| `max_reintentos` | `3` |
| `agente_ejecutor` | `agent-dotnet-api` |

En el nivel superior: `ticket_id`, `perfil: "ssd01"`, `generado_por: "speckit-a-harness"`
y, solo si hace falta, `fuera_de_ejecucion: [{"ref": "FR-xxx", "motivo": "…"}]` para un
FR que **ninguna tarea implementa**, con el motivo. Un FR negativo (*MUST NOT*) que una
regla de `rules.json` vigila se ancla en la fase que crea los endpoints, no va aquí.

**Frase fija de evidencia test-first** (literal, sin cambiar una letra):

> Evidencia test-first: el `resultado.md` del primer intento de esta fase (`.harness/tickets/<ticket_id>/<fase>/intento_1/resultado.md`) contiene, en una sección `## Rojo`, la salida de `dotnet test` con las pruebas nuevas fallando, antes de la implementación; los intentos siguientes lo referencian y no lo repiten

El escéptico no recibe `resultado.md` ni ve `.harness/` en el diff: escrita en el
criterio, la exigencia le llega y la puede verificar leyendo el archivo. Se fija en el
**primer** intento porque en un reintento las pruebas y el código del intento anterior
siguen en el árbol de trabajo y el rojo ya no se puede reproducir. `<ticket_id>` y
`<fase>` se dejan tal cual: el escéptico conoce ambos.

**Una fase sin código** (p. ej. Polish que solo ejecuta y comprueba) no deja nada que
`dotnet_build` pueda compilar ni que el escéptico pueda leer en el diff. Su
`criterio_exito` se escribe sobre un entregable versionado de la fase (un documento con
la evidencia) y lo que solo comprueba un humano va en la prueba manual.

## `plan.md` (para el humano)

```markdown
# Plan del ticket <id> — <feature>

Traducido de [tasks.md](<ruta relativa a tasks.md>) por speckit-a-harness. La spec no se repite aquí.

| Fase | Título | Tareas | Depende de | Prueba manual |
|---|---|---|---|---|
| fase_1 | Setup | Txxx–Tyyy | — | sí: <qué se comprueba> |

FR fuera de la ejecución: <ninguno | FR-xxx: motivo>.
```

## Lo que no hace

- No reescribe, junta, parte ni re-planifica tareas. Si `tasks.md` está mal, se corrige
  `tasks.md` (o se vuelve a correr `/speckit-tasks`) y se traduce de nuevo.
- No abre fases.
- No copia contenido de la spec a `ticket.md` ni a `plan.md`.
