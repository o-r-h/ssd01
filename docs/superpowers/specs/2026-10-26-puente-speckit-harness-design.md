# Diseño: puente spec-kit → harness

**Fecha**: 2026-10-26 | **Repo**: `ssd01` | **Feature piloto**: `specs/001-cuentas-bancarias`

## Intención

En un ticket real, el desarrollador quiere este recorrido: llega el ticket, se trabaja con spec-kit hasta `tasks.md` (specify → clarify → plan → tasks), y desde ahí **el harness toma el control y ejecuta** fase por fase, en lugar de `/speckit-implement`.

Cada lado aporta lo que hace mejor:

- **spec-kit** define el qué y el cómo: spec aclarada, decisiones técnicas con su porqué, contrato y tareas trazables.
- **El harness** (`C:\AZZULE\IA harness`, desplegado en `~/.claude/`) ejecuta con control:
  - hook en vivo;
  - checks deterministas;
  - escéptico con contexto aislado;
  - prueba manual con gate humano;
  - reflector que propone lecciones para la biblioteca.

`/speckit-implement` no tiene nada de esto: confía en lo que la IA dice que hizo.

Este repo es un **ejercicio de aprendizaje**. El puente se construye y se prueba aquí con la feature 001, y se documenta en `mis_notas/`.

## Objetivos

1. Abrir un ticket del harness a partir de una feature de spec-kit con `tasks.md` terminado, sin pasar por `task-planner`.
2. Generar un `plan.json` válido según el contrato del harness (`cli.py validate --contrato plan`). Cada fase debe estar anclada en las secciones exactas de la spec, el research y el contrato que necesita.
3. Ejecutar la feature 001 completa con el ciclo de fase **de producción sin cambios**: `/fase`, `run-checks`, escéptico, guion de prueba, `/fase-ok` o `/fase-fallo`, reflector y hallazgos.
4. Dejar el puente documentado y reutilizable para la siguiente feature o el siguiente ejercicio.

## No-objetivos

- Cambiar el harness de producción (`~/.claude/` ni `C:\AZZULE\IA harness`).
- Cambiar spec-kit (skills `speckit-*` ni plantillas de `.specify/`).
- Automatizar la decisión humana: el gate por fase y la decisión sobre hallazgos siguen siendo manuales.
- Hacer el puente genérico para otros stacks. El perfil es de .NET 10. La parte de apertura del ticket debería servir para cualquier perfil, pero no se prueba con otros.

## Anti-objetivos (fracaso aunque funcione)

- **Perder el control manual por fase.** Es lo que permite verificar resultados y mejorar el harness con retroalimentación. Si el puente salta el gate, la prueba manual o el reflector, fracasó.
- **Tocar producción "solo un poquito".** El harness está probado en producción con tickets reales de NAS. Todo cambio vive en este repo.
- **Planificar dos veces.** Si el puente vuelve a generar el plan desde cero en lugar de traducir `tasks.md`, se pierde la trazabilidad de spec-kit.

## Restricciones

- **Los hooks de producción son globales** (`~/.claude/settings.json`: `check_rules.py` en PostToolUse y `gate_phase.py` en Stop) y **solo se activan si el proyecto tiene `.claude/rules.json`**. Darle un perfil a este repo los activa aquí. Eso es *usar* producción, no modificarla, y el diseño lo acepta.
- **El harness compara contra `HEAD`** (`lib/gitdiff.py`): `run-checks` y el escéptico ven solo lo que no está en commit. No se puede hacer commit en medio de una fase.
- **Contrato de `plan.json`** (`harness/hooks/lib/contracts.py`, `validate_plan`):
  - El plan exige `ticket_id`, `perfil` y `fases` (no vacía).
  - Cada fase exige `id` (formato `fase_N`), `titulo`, `criterio_exito`, `pasos` (no vacía), `anclajes` (`{ref, confianza: verificado|por_confirmar}`), `checks_deterministas` (que existan en `rules.json`), `herramientas_permitidas` (no vacía), `depende_de`, `prueba_manual.requerida` (booleano) y `max_reintentos` (de 1 a 10). `agente_ejecutor` es opcional y debe existir en `.claude/agents/`.
- **Constitución v1.0.0** (`.specify/memory/constitution.md`): Principio II, test-first con pruebas de integración; Principio III, YAGNI y cada dependencia justificada; Principio IV, secretos fuera del código. La sección "Flujo de trabajo" dice hoy "specify, plan, tasks, implement" y "cada tarea se cierra con un commit propio", y **las dos cosas cambian** (ver Decisiones).
- Stack de la feature 001, fijado por el enunciado: .NET 10 (SDK 10.0.302 instalado), ASP.NET Core Web API, SQLite y xUnit.

## Decisiones tomadas por el desarrollador

1. **Puente con este mismo ejercicio**, no en uno posterior.
2. **El harness de producción no se toca.** Lo que cambie vive en este repo, como copia o pieza nueva.
3. **Se conserva completo el control manual por fase.**
4. **Una fase del harness por cada fase de `tasks.md`** (Setup, Foundational, una por historia de usuario, Polish), no una por tarea. Para la 001 son unas 5 fases.
5. **El commit se hace al aprobar cada fase**, no por tarea. Se enmienda la constitución.
6. **El ejecutor no lee la spec completa.** Conoce el stack y *cómo* está organizada una feature de spec-kit. Cada fase de `plan.json` trae en `anclajes` las secciones exactas que necesita (p. ej. `specs/001-cuentas-bancarias/spec.md#FR-003`, `research.md#R2`, `contracts/openapi.yaml#/paths/~1cuentas`). Los mismos anclajes los recibe el escéptico.
7. **Test-first dentro de la misma fase.** Pruebas e implementación van juntas, porque el check `dotnet_build` falla con pruebas en rojo. El ejecutor deja en `intento_N/resultado.md` la salida de `dotnet test` **en rojo, antes de implementar**, como evidencia para el escéptico.
8. **Gate humano en todas las fases**, incluidas Setup, Foundational y Polish. Si `prueba_manual.requerida` fuera `false`, el CLI aprobaría la fase solo con el escéptico (`cli.py`, `record-veredicto`). Esas fases llevan una prueba manual corta según lo que entreguen: "la solución compila", "la API no arranca sin `Auth:ApiKey`", "sin credencial responde 401".
9. **Lecciones de la biblioteca.** Las que corrigen piezas de este repo (`rules.json`, checks, `agent-dotnet-api`, el skill del puente) se aplican aquí. Las que corrigen piezas de producción (escéptico, reflector, `ticket-loop`, hooks, CLI) quedan en la biblioteca marcadas como **candidatas a producción**. El desarrollador decide después si las lleva a `C:\AZZULE\IA harness`, con su propio test.

## El diseño

### Piezas nuevas (todas dentro de `ssd01/`)

```
ssd01/
├── .claude/
│   ├── rules.json                         perfil: activa el harness en este repo
│   ├── agents/agent-dotnet-api.md         ejecutor del perfil
│   ├── checks/dotnet_build.py             copia de profiles/editornotificaciones/checks/
│   ├── commands/ticket-abrir-sdd.md       /ticket-abrir-sdd <carpeta de la feature>
│   └── skills/speckit-a-harness/
│       ├── SKILL.md                       apertura del ticket: traduce tasks.md a plan.json
│       └── verificar_traduccion.py        check determinista de la traducción
├── .gitignore                             + .harness/
└── docs/puente-speckit-harness.md         cómo se usa el puente (documentación final)
```

`.claude/biblioteca/` la crea el CLI al aprobar el primer hallazgo y se versiona con el repo.

### 1. Perfil

**`rules.json`**. Usa el formato de `profiles/editornotificaciones/rules.json`, con pocas reglas y todas sacadas de la constitución:

| id | Qué detecta | Archivos / excluir | Severidad | Principio |
|---|---|---|---|---|
| `no_secretos` | Un valor literal para la API key o una credencial | `.cs`, `.json`; excluye `tests/`, `.claude/`, `specs/` | error | IV |
| `dep_nueva` | `<PackageReference` agregado | `.csproj` | **warning**: el escéptico lo contrasta con la lista justificada en `plan.md` | III |
| `solo_dos_endpoints` | `Map(Put\|Delete\|Patch)` o rutas fuera de `/cuentas` | `.cs`; excluye `tests/` | error | Restricción de alcance |

`audit_comments.requerido: false` (repo nuevo con git, sin bloques `[B]/[E]`). `checks_estructurales: ["dotnet_build"]`.

Notas verificadas en el motor de reglas (`~/.claude/hooks/lib/checks.py`):

- `prohibido` filtra solo por extensión y por las carpetas de `excluir`, no por nombre de archivo. Por eso `no_secretos` aplica a todo `.json`, y excluye `.claude/` para que `rules.json` no choque con su propio patrón.
- `no_new_deps` compara nombres de archivo exactos (`vigilar`). Atarlo a los `.csproj` de esta feature haría el perfil no reutilizable. Por eso se usa una regla `prohibido` por extensión, `dep_nueva`.
- `tests/` queda excluido de `no_secretos` porque `ApiFactory` inyecta una API key de prueba literal (research R8). Hay precedente: editornotificaciones excluye su carpeta de pruebas.

**`checks/dotnet_build.py`**: copia sin cambios del check de editornotificaciones. Busca `*.sln`/`*.slnx` en la raíz y corre `dotnet build` y `dotnet test`. Por eso la fase Setup tiene que dejar `CuentasBancarias.slnx` en la raíz.

**`agents/agent-dotnet-api.md`**: el ejecutor. Usa como modelo de forma `agent-notif-api.md`. Debe contener:

- el stack y sus versiones;
- cómo está organizada una feature de spec-kit (`specs/<feature>/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`) y la regla de **leer solo los anclajes de la fase**;
- el procedimiento test-first con evidencia en rojo en `resultado.md`;
- la regla de **no hacer commit** durante la fase;
- los guardrails de `rules.json` explicados en prosa.

No lleva rutas ni contenido de la feature 001.

### 2. Apertura del ticket: `/ticket-abrir-sdd`

El comando invoca el skill `speckit-a-harness`. El skill sigue los pasos de "Al abrir un ticket" de `~/.claude/skills/ticket-loop/SKILL.md` y cambia tres cosas:

- el paso 1: no pide un requerimiento, porque lo toma de la feature;
- el paso 3: el id no lleva el prefijo `ISR-`;
- el paso 4: reemplaza task-planner por la traducción de `tasks.md`.

Los pasos 0 y 5 quedan iguales.

0. `CLI hallazgos-pendientes`, igual que producción.
1. Verifica que la carpeta de la feature tenga `spec.md`, `plan.md` y `tasks.md`. Si falta `tasks.md`, se detiene y pide correr `/speckit-tasks`.
2. Escribe `.harness/tickets/<id>/ticket.md`: un resumen de la feature con enlaces a `spec.md`, `plan.md` y `tasks.md`. No copia su contenido.
3. Pregunta una sola vez el id de ticket, el nombre del desarrollador y la fecha (`DD-MM-YYYY`). Para este ejercicio el id es `SSD-001`, porque el CLI no valida el formato.
4. `CLI open-ticket --ticket-id <id> --nroticket <nro> --desarrollador … --fecha … --perfil ssd01`.
5. **Traduce `tasks.md` a `plan.json` y `plan.md`** (ver la tabla de traducción). Si existe `.claude/biblioteca/INDEX.md`, lo lee como hoy lo hace task-planner. Cada lección aprobada cuya señal coincida con una fase se agrega a sus `anclajes` como `{"ref": ".claude/biblioteca/entradas/<archivo>.md", "confianza": "por_confirmar"}`. Las rechazadas no se usan.
6. Corre `verificar_traduccion.py` y `CLI validate --contrato plan`. Si alguno falla, corrige y repite. **No se abre ninguna fase con un plan inválido.**
7. Muestra `plan.md` y termina. Desde aquí se usa `/fase fase_1` de producción.

**Tabla de traducción** (fase de `tasks.md` → fase de `plan.json`):

| Campo de `plan.json` | Origen |
|---|---|
| `id` | `fase_N`, en el orden de las fases de `tasks.md` |
| `titulo` | El título de la fase en `tasks.md` |
| `pasos` | Una línea por tarea, con su id (`T012 …`) y la ruta de archivo que nombra. Al final, el paso fijo: "ESCRIBE intento_N/resultado.md con la evidencia, incluida la corrida en rojo si la fase tiene pruebas" |
| `criterio_exito` | Para fases de historia: el **Independent Test** y los **Acceptance Scenarios** de esa historia en `spec.md`, **literales**, más el Checkpoint de `tasks.md`. Para Setup, Foundational y Polish: el Checkpoint y el propósito de la fase. **En toda fase que agregue pruebas**, se suma la frase fija: "Evidencia test-first: `intento_N/resultado.md` de esta fase contiene, en una sección `## Rojo`, la salida de `dotnet test` con las pruebas nuevas fallando, antes de la implementación". El escéptico de producción solo recibe el diff, `criterio_exito`, `anclajes`, `checks.json` y `historial_fallos`; no recibe `resultado.md`, y `.harness/` no entra al diff. Escrita en el criterio, la exigencia le llega y la puede verificar leyendo el archivo |
| `anclajes` | Cada FR, decisión de research (R1…R8), sección de `data-model.md` o ruta del contrato que citan las tareas de la fase, como `ref` con ruta y ancla, `confianza: "verificado"` (son documentos ya revisados en clarify y plan) |
| `checks_deterministas` | `["dotnet_build"]` más las reglas que apliquen, o los grupos de `rules.json` |
| `herramientas_permitidas` | Lectura, edición y Bash para `dotnet` |
| `depende_de` | Lo que declara la sección "Dependencies & Execution Order" de `tasks.md` |
| `prueba_manual` | `requerida: true` en **todas** las fases (decisión 8), `url` (la URL local de la API) y `datos` (cómo configurar `Auth:ApiKey` y levantar la API, según `quickstart.md`). El guion de clics lo deriva el orquestador de `criterio_exito` (ticket-loop, paso 6), y el render solo usa `url` y `datos` (`lib/prueba_manual.py`). Por eso los escenarios van literales en el criterio y no como pasos aparte |
| `max_reintentos` | 3 |
| `agente_ejecutor` | `agent-dotnet-api` |

`plan.md` (para el humano): una tabla con las fases, sus tareas, su dependencia y si llevan prueba manual, con enlace a `tasks.md`. No repite el contenido de la spec.

**Requisito sobre `tasks.md`**: para que existan anclajes, `/speckit-tasks` se corre con el argumento *"cada tarea cita entre paréntesis los FR, las decisiones de research (R#) y las rutas del contrato que implementa"*. Es un argumento, no un cambio a spec-kit.

**`verificar_traduccion.py`** (check determinista, Python solo con stdlib, como el harness). Recibe la carpeta de la feature y el `plan.json`, y falla si:

- una tarea `Txxx` de `tasks.md` no aparece en ningún `pasos`, o aparece en más de una fase;
- un FR de `spec.md` no está anclado en ninguna fase (excepto los que el `plan.json` declare explícitamente como fuera de la ejecución, con motivo);
- una fase de historia de usuario tiene `criterio_exito` que no contiene el texto literal de su Independent Test;
- una fase con tareas de prueba no trae en `criterio_exito` la frase fija de evidencia test-first.

Es la forma barata de verificar el juicio del modelo, siguiendo la idea central del harness.

### 3. Ejecución

Sin cambios. Se usa el ciclo de producción: `/fase fase_N`, `/fase-ok`, `/fase-fallo`, `/hallazgo-*`. El ejecutor es `agent-dotnet-api` y el escéptico y el reflector son los de `~/.claude/agents/`.

**Al aprobar cada fase**, el desarrollador (o Claude, a pedido suyo) hace **un commit** con:

- el código de la fase;
- los checkboxes `[x]` de sus tareas en `tasks.md`;
- `.claude/biblioteca/`, si cambió.

Formato del mensaje: `feat(001): fase_N <título>`.

**Al cerrar cada fase**, después de que el desarrollador decide sobre los hallazgos (`/hallazgo-ok` y demás):

- Las lecciones aprobadas cuyo `componente` apunta a una pieza de este repo se aplican en el commit de la fase siguiente, o en uno propio si no hay fase abierta.
- Las que apuntan a una pieza de producción se anotan en `docs/candidatas-a-produccion.md`, con su referencia `TICKET/fase_N/hN`, la pieza afectada y la evidencia. Nada se cambia en `~/.claude/`.

### 4. Enmienda a la constitución (v1.0.0 → v1.1.0)

En la sección "Flujo de trabajo":

- "El flujo Spec Kit es obligatorio: specify, plan, tasks, implement" → "specify, clarify, plan y tasks con Spec Kit; la ejecución, fase por fase, bajo el harness".
- "Cada tarea de tasks.md se cierra con un commit propio" → "Cada fase del harness se cierra con un commit propio al ser aprobada".

Versión MINOR: cambia una regla de flujo, no un principio.

### 5. Documentación

- `docs/puente-speckit-harness.md`: cómo se usa el puente, de punta a punta, para la siguiente feature.
- `mis_notas/plan-notas.md`: actualizar la sección del puente con lo construido.
- `mis_notas/`: una nota nueva al terminar la ejecución, con lo aprendido del puente y los hallazgos.

## Orden de trabajo

1. Enmienda a la constitución y actualización a mano de la fila "Flujo de trabajo" del Constitution Check de `plan.md`, con la nota "re-verificado contra v1.1.0". No se vuelve a correr `/speckit-plan`, porque regeneraría research, contrato y quickstart, que ya están aprobados.
2. `.gitignore`: `.harness/`, `bin/`, `obj/`, `*.db`, `TestResults/`. `run-checks` toma todos los archivos sin rastrear (`gitdiff.py`, `--untracked-files=all`), así que sin esto los archivos generados por el build entrarían a los checks, al diff del escéptico y al commit.
3. Perfil: `rules.json`, `checks/dotnet_build.py` y `agents/agent-dotnet-api.md`.
4. Skill `speckit-a-harness`, `verificar_traduccion.py` y comando `/ticket-abrir-sdd`.
5. `/speckit-tasks` con el argumento de trazabilidad.
6. **Commit de todo lo anterior** (artefactos de plan y tasks, puente, perfil, notas). Si no se hace, todo eso aparecería en el diff de `fase_1` y el escéptico lo juzgaría como parte de la fase.
7. `/ticket-abrir-sdd specs/001-cuentas-bancarias` y validación del plan.
8. Ejecución fase por fase con el harness.
9. Documentación final.

Los pasos 1 a 6 se hacen fuera del harness (todavía no hay ticket abierto). Desde el paso 7, todo cambio de código pasa por fases.

## Decisiones del diseñador (revisables)

- **Nombre del perfil `ssd01` y del agente `agent-dotnet-api`.**
- **La traducción la hace el modelo (skill) y la verifica un script**, en lugar de un parser determinista. `tasks.md` lo escribe un modelo y su formato varía, así que un parser sería frágil. El script verifica lo que importa: que no se pierda ninguna tarea ni ningún FR.
- **`confianza: "verificado"` para anclajes a documentos de spec-kit**, porque fueron revisados por el humano en clarify y plan. Los anclajes a código no existen en la 001 (repo vacío).
- **`max_reintentos: 3`.**
- **Las candidatas a producción se registran en `docs/candidatas-a-produccion.md`**, no en un campo nuevo de `hallazgos.json`, para no cambiar el contrato del CLI.
- **Versión 1.1.0** para la enmienda.

## Lo que queda al constructor

- El texto exacto de las reglas regex de `rules.json`.
- La redacción del agente y del skill, siguiendo el estilo de los equivalentes de producción.
- Cómo `verificar_traduccion.py` reconoce tareas (`T\d{3}`), FR (`FR-\d{3}[a-z]?`) e Independent Test en el markdown.
