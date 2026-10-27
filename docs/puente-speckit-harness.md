# Puente spec-kit → harness

Cómo llevar una feature de spec-kit hasta código terminado **bajo el harness**, en lugar de `/speckit-implement`.

- **spec-kit** decide el qué y el cómo: spec aclarada, plan con decisiones técnicas, contrato y tareas trazables.
- **El harness** ejecuta fase por fase con control:
  - reglas que se revisan en vivo (hook);
  - checks deterministas (build y pruebas);
  - un escéptico con contexto aislado;
  - una prueba manual con gate humano;
  - un reflector que propone lecciones para la biblioteca.

El harness de producción (`~/.claude/`, fuente en `C:\AZZULE\IA harness`) **no se modifica**: este repo lo usa tal cual. Lo único propio del repo es el perfil y la apertura del ticket.

Diseño completo: [superpowers/specs/2026-10-26-puente-speckit-harness-design.md](superpowers/specs/2026-10-26-puente-speckit-harness-design.md).

## Piezas del repo

| Pieza | Para qué |
|---|---|
| `.claude/rules.json` | Perfil `ssd01`. Su existencia activa los hooks del harness en este repo. Reglas sacadas de la constitución: `no_secretos`, `dep_nueva`, `solo_dos_endpoints` (grupo `constitucion`) |
| `.claude/checks/dotnet_build.py` | Check estructural: `dotnet build` + `dotnet test` de la solución en la raíz. Copia del perfil editornotificaciones |
| `.claude/agents/agent-dotnet-api.md` | Ejecutor de las fases. Lee solo los anclajes de su fase y trabaja test-first |
| `.claude/commands/ticket-abrir-sdd.md` + `.claude/skills/speckit-a-harness/` | Abre el ticket traduciendo `tasks.md` a `plan.json` |
| `.claude/skills/speckit-a-harness/verificar_traduccion.py` | Verifica la traducción sin modelo |
| `.claude/tests/` | Pruebas de las reglas (contra el motor real) y del verificador: `python -m unittest discover -s .claude/tests` |
| `.gitignore` | Deja fuera del diff de cada fase `.harness/`, `bin/`, `obj/`, `*.db`, `TestResults/` y `__pycache__/` |
| `docs/candidatas-a-produccion.md` | Lecciones que corrigen piezas de producción, para decidirlas después |

## De punta a punta

### 1. Diseño con spec-kit

```text
/speckit-specify  →  /speckit-clarify  →  /speckit-plan  →  /speckit-tasks <argumento>
```

`/speckit-tasks` se corre **siempre** con este argumento:

> cada tarea cita entre paréntesis los FR, las decisiones de research (R#) y las rutas del contrato que implementa

Las citas son los anclajes que recibe cada fase. Sin ellas, el ejecutor tendría que leer la spec completa.

Tres cosas a revisar en `tasks.md` antes de seguir:

- **Una tarea por línea**, en formato `- [ ] T001 …`. El verificador cuenta las tareas con una regex.
- **Encabezados `## Phase N: …`** (o `## Fase N: …`). Las historias van como `User Story N` (o `Historia de usuario N`).
- **Una prueba va en la fase donde puede fallar.** Test-first exige mostrar la corrida en rojo. Una prueba que ya pasaría al escribirla (p. ej. una de regresión en Polish) no puede dar esa evidencia.
- **Cada fase entrega algo versionado.** El harness juzga el diff. Una fase que solo ejecuta y comprueba (Polish) entrega un documento con la evidencia, y lo que solo puede comprobar un humano va en su prueba manual.
- **Las tareas de Setup se escriben contra la herramienta real.** Por ejemplo, `dotnet new web` trae un `MapGet("/")` que la regla de alcance rechaza, y sin `dotnet user-secrets init` el `set` falla.

### 2. Commit de todo el diseño

El harness compara contra `HEAD`. Lo que no esté en commit aparece en el diff de `fase_1`, y el escéptico lo juzgaría como parte de la fase.

```bash
git add specs/<feature>/ mis_notas/
git commit -m "spec(<feature>): add traceable tasks"
git status --porcelain   # debe quedar vacío
```

### 3. Abrir el ticket

```text
/ticket-abrir-sdd specs/<feature>
```

Pide **una vez** el id, el número de ticket, el desarrollador y la fecha. Después escribe `.harness/tickets/<id>/plan.json` y `plan.md`, y verifica las dos cosas:

```bash
python .claude/skills/speckit-a-harness/verificar_traduccion.py specs/<feature> .harness/tickets/<id>/plan.json
python "$HOME/.claude/hooks/cli.py" validate --contrato plan --archivo .harness/tickets/<id>/plan.json
```

| El verificador falla si… | Por qué importa |
|---|---|
| una tarea falta en `pasos` o está en dos fases | no se pierde ni se duplica trabajo |
| una fase del plan mezcla tareas de dos fases de `tasks.md`, o no traduce ninguna | una fase del harness es una fase de `tasks.md` (ni se parte ni se junta) |
| un FR no está anclado (salvo `fuera_de_ejecucion` con motivo) | ningún requisito queda sin dueño |
| una fase de historia no trae literal su Independent Test | la prueba manual sale del `criterio_exito` |
| una fase con pruebas no exige la evidencia `## Rojo` | test-first se puede verificar, no solo afirmar |
| una fase no tiene `prueba_manual.requerida: true` | el gate humano no se salta nunca |

Si falla por la forma de `tasks.md`, **se corrige `tasks.md`, no el verificador**.

### 4. Ejecutar fase por fase

Se usa el ciclo de producción, sin cambios:

```text
/fase fase_1      → ejecutor, run-checks, escéptico, guion de prueba manual
                  → el harness se detiene y espera
/fase-ok          o   /fase-fallo <paso> "<lo observado>"
```

**Al aprobar cada fase**, se hace un commit con:

- el código de la fase;
- los `[x]` de sus tareas en `tasks.md`;
- `.claude/biblioteca/`, si cambió.

```bash
git commit -m "feat(<feature>): fase_N <título>"
```

El ejecutor nunca hace commit. Un commit a mitad de fase esconde el trabajo de `run-checks` y del escéptico.

### 5. Hallazgos del reflector

Al cerrar cada fase, el reflector propone lecciones y tú decides cada una: `/hallazgo-ok`, `/hallazgo-editar`, `/hallazgo-no` o `/hallazgo`. Según el `componente` que corrige la lección:

| Corrige… | Qué se hace |
|---|---|
| una pieza de **este repo** (`rules.json`, un check, `agent-dotnet-api`, el skill del puente) | se aplica aquí, en el commit de la fase siguiente o en uno propio |
| una pieza de **producción** (escéptico, reflector, `ticket-loop`, hooks, CLI) | se anota en [candidatas-a-produccion.md](candidatas-a-produccion.md). Nada se cambia en `~/.claude/` |

## Ejemplo: la feature 001

- `tasks.md` tiene 17 tareas en 5 fases (Setup, Foundational, US1, US2, Polish), y todas citan sus FR, R# y rutas del contrato.
- El ticket es `SSD-001`. La salida del verificador: `traducción: OK (17 tareas, 15 FR, 5 fases)`.
- `fase_4` (US2) depende también de `fase_3`, porque la prueba de durabilidad crea la cuenta con `POST /cuentas`.
- La siguiente acción es `/fase fase_1`.
