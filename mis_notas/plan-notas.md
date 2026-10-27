# Plan

## Qué es el paso plan en Spec Kit

Es la fase que convierte el **qué** (la spec) en el **cómo**: stack, decisiones técnicas, modelo de datos y contratos. Va después de clarify y antes de tasks. Sigue sin escribir código: produce documentos de diseño que luego `/speckit-tasks` convierte en tareas.

La diferencia con la spec es de audiencia. La spec habla de comportamiento y la puede leer alguien de negocio. El plan habla de tecnología y lo lee quien va a construir.

## Qué hace el skill /speckit-plan

1. Corre `setup-plan.ps1`, que copia la plantilla a `specs/<feature>/plan.md`.
2. Lee la spec y la constitución.
3. Llena el **Technical Context**: lenguaje, dependencias, almacenamiento, pruebas, plataforma, metas de rendimiento y restricciones. Lo que no sabe lo marca `NEEDS CLARIFICATION`.
4. Llena el **Constitution Check**: un gate que contrasta el plan con cada principio. Si algo viola la constitución sin justificación, el plan se detiene (ERROR).
5. **Fase 0, `research.md`**: resuelve cada incógnita técnica con el formato *Decision / Rationale / Alternatives considered*.
6. **Fase 1, diseño**: genera `data-model.md`, `contracts/` y `quickstart.md`.
7. Vuelve a pasar el Constitution Check con el diseño ya hecho.

No crea `tasks.md`; eso es de la fase siguiente.

## Lo que hicimos en el ejercicio (feature 001-cuentas-bancarias)

**El stack no estaba en el repo.** La constitución dice "el stack definido en el enunciado del ejercicio", pero el enunciado nunca se guardó. Hubo que preguntarlo: .NET 10, ASP.NET Core Web API, SQLite y xUnit. Lección: si la constitución remite a un documento, ese documento tiene que estar en el repo.

Archivos generados en `specs/001-cuentas-bancarias/`:

| Archivo | Contenido |
|---|---|
| `plan.md` | Technical Context, Constitution Check (todo PASS), estructura de carpetas del código |
| `research.md` | 8 decisiones técnicas con su porqué y las alternativas descartadas |
| `data-model.md` | Entidad Cuenta, esquema SQLite, tabla de cada error de validación posible |
| `contracts/openapi.yaml` | Contrato de `POST /cuentas` y `GET /cuentas/{id}` (exigido por el Principio I) |
| `quickstart.md` | Cómo comprobar la feature: `dotnet test` y ejemplos con `curl` |

### Decisiones que vale la pena recordar

- **Minimal API, sin ORM, sin capa de servicios.** Dos endpoints y una tabla no justifican más (Principio III, YAGNI). Cada dependencia se justificó por escrito en el plan.
- **El cuerpo se valida como JSON crudo, no como clase tipada.** Esto salió directo de las decisiones de clarify:
  - ASP.NET Core acepta por defecto `"1000"` (texto) como número, y en clarify decidimos rechazarlo.
  - Con una clase tipada, un error de tipo corta la lectura y no se pueden reportar todos los errores juntos (FR-003a).
- **La credencial se revisa en un middleware, no en un filtro.** En Minimal API los filtros corren después de leer el cuerpo: alguien sin credencial que mande un JSON roto recibiría un 400 en vez de un 401, y eso le da pistas.
- **El saldo se guarda en centavos (entero).** SQLite no tiene tipo decimal; `REAL` redondea mal el dinero.
- **El identificador es un GUID v7.** Un identificador con formato inválido devuelve el mismo 404 que uno inexistente, para no revelar nada.
- **Sin credencial configurada, la API no arranca** (fail-closed).

## Lo que aprendí

- **Las respuestas de clarify cambian el diseño técnico.** Dos preguntas que parecían de detalle (texto numérico y "listar todos los errores") obligaron a descartar la forma estándar de recibir datos en ASP.NET Core. Si no se hubieran aclarado antes, se habrían descubierto en implement.
- **El Constitution Check es la constitución trabajando.** Cada principio se convierte en una fila verificable del plan. El Principio III obligó a justificar cada dependencia y cada clase que no fuera estrictamente necesaria.
- **`research.md` documenta lo que se descartó.** Saber por qué no se usó EF Core o controladores evita volver a discutirlo después.
- **La IA no se configura en plan.** Plan no define skills ni agentes. Los skills de spec-kit se instalan una vez con `specify init`. En versiones anteriores, plan actualizaba `CLAUDE.md` con el stack, pero la versión 0.13.4 ya no lo hace.

## Pregunta que surgió: spec-kit y mi harness

spec-kit y el harness (`C:\AZZULE\IA harness`) cubren parte del mismo terreno:

| Etapa | spec-kit | Harness |
|---|---|---|
| Qué se construye | `specify` + `clarify` → `spec.md` | `ticket.md` |
| Cómo se construye | `plan` + `tasks` | `task-planner` → `plan.md` + `plan.json` |
| Ejecución | `implement` (confía en la IA) | Ciclo por fase: ejecutor → checks → escéptico → prueba manual → gate humano → reflector |

**Decisión: hacer el puente con este mismo ejercicio.** spec-kit define hasta `tasks.md` y el harness toma el control de la ejecución, en lugar de `/speckit-implement`.

Reglas del puente:

1. **El harness de producción no se toca.** Lo que cambie vive en una copia dentro de este repo.
2. **Se conserva el control manual por fase.** Es lo que permite verificar resultados y mejorar el harness con los hallazgos del reflector.

Lo que encontré al revisar el harness:

- Los hooks son globales, pero **solo se activan si el proyecto tiene `.claude/rules.json`**. Darle un perfil a este repo activa el harness aquí sin modificarlo.
- **Solo cambia la apertura del ticket.** Todo el ciclo de fase funciona con cualquier `plan.json` válido, venga o no de `task-planner`. La copia se reduce a un comando y un skill propios en `ssd01/.claude/` que arman `plan.json` a partir de `tasks.md`.
- El perfil `editornotificaciones` ya usa .NET 10 + ASP.NET Core + SQLite + xUnit, y su check `dotnet_build` (build + pruebas) sirve de base.

Decisiones tomadas:

- **Cada fase del harness corresponde a una fase de `tasks.md`**, más o menos una por historia de usuario (unas 5 en total), no una por tarea. Con una por tarea serían unos 20 gates manuales.
- **El commit se hace al aprobar cada fase, no por tarea.** El harness compara contra `HEAD`: un commit en medio de una fase esconde el trabajo a `run-checks` y al escéptico. Hay que enmendar la regla de la constitución que pedía un commit por tarea.

Pendiente: diseñar y construir el puente.
