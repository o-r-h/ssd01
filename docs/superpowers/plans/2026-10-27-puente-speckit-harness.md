# Puente spec-kit → harness: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que la feature 001 pueda abrirse como ticket del harness a partir de su `tasks.md` y quede lista para `/fase fase_1`, sin tocar el harness de producción.

**Architecture:** Todo vive en `ssd01/.claude/`. Hay un perfil (`rules.json`, check `dotnet_build`, agente ejecutor) que activa los hooks globales de producción en este repo. Hay un skill más un comando que traducen `tasks.md` a `plan.json`, y un script de stdlib que verifica esa traducción. La ejecución posterior usa el ciclo de producción sin cambios.

**Tech Stack:** Python 3.12 stdlib (`unittest`, `re`, `json`), igual que el harness. Markdown para el agente, el skill y el comando. La feature que se va a ejecutar es .NET 10 + ASP.NET Core + SQLite + xUnit.

**Spec:** `docs/superpowers/specs/2026-10-26-puente-speckit-harness-design.md`

## Global Constraints

- Nunca modificar `~/.claude/` ni `C:\AZZULE\IA harness`. Leerlos e importarlos en pruebas sí está permitido.
- No modificar los skills `speckit-*` ni las plantillas de `.specify/`.
- Los scripts son Python solo con stdlib.
- Las rutas de la feature no aparecen en piezas reutilizables (agente, skill, comando, script). La única excepción es la documentación de ejemplo.
- Perfil `ssd01`, agente `agent-dotnet-api`, `max_reintentos: 3` y `prueba_manual.requerida: true` en todas las fases.
- Ticket del ejercicio: `SSD-001`. El id, el desarrollador y la fecha (`DD-MM-YYYY`) se preguntan una sola vez y nunca se inventan.
- `CLI` = `python "$HOME/.claude/hooks/cli.py"`.
- Frase fija de test-first (en `verificar_traduccion.py` y en el skill, idéntica en los dos): ``Evidencia test-first: `intento_N/resultado.md` de esta fase contiene, en una sección `## Rojo`, la salida de `dotnet test` con las pruebas nuevas fallando, antes de la implementación``
- Todo lo de este plan debe quedar en commit antes de `/fase fase_1`. El harness compara contra `HEAD`.
- Commits con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` al final.
- Desde que existe `.claude/rules.json` (Task 3), los hooks de producción se activan en este repo. Es lo esperado.

## Review Focus

1. **Archivos generados que entran al diff de una fase** (`bin/`, `obj/`, `*.db`, `TestResults/`, `__pycache__/` de los checks y las pruebas Python). Se espera que `git check-ignore` los reconozca. Prueba: Task 2, paso 2.
2. **Falsos positivos de las reglas sobre código legítimo**: `builder.Configuration["Auth:ApiKey"]`, `"ApiKey": ""` en `appsettings.json`, `const string Header = "X-Api-Key";` y `app.MapGet("/cuentas/{id}", …)`. Ninguno debe marcarse. Prueba: Task 3, `test_negativos_*`.
3. **`rules.json` chocando con su propio patrón, o la API key de prueba de `ApiFactory`** (research R8). El motor real de producción no debe marcarlos. Prueba: Task 3, `test_motor_respeta_excluir`.
4. **`tasks.md` con forma distinta a la plantilla**: checkboxes ya marcados `[x]` tras aprobar fases, el Independent Test partido en otras líneas, títulos en español. La verificación debe seguir funcionando. Prueba: Task 5, `test_tareas_marcadas_x`, `test_independent_test_con_otro_salto_de_linea` y `test_titulos_en_espanol`.
5. **`FR-002` frente a `FR-002a`**: anclar el sufijo no cubre el FR base. Prueba: Task 5, `test_fr_con_sufijo_no_cubre_el_base`.

---

## Mapa de archivos

| Archivo | Responsabilidad | Task |
|---|---|---|
| `.specify/memory/constitution.md` | Enmienda v1.1.0 (Flujo de trabajo) | 1 |
| `specs/001-cuentas-bancarias/plan.md` | Fila "Flujo de trabajo" re-verificada | 1 |
| `.gitignore` | Nada generado entra al diff del harness | 2 |
| `.claude/rules.json` | Perfil `ssd01`: reglas sacadas de la constitución | 3 |
| `.claude/checks/dotnet_build.py` | Copia sin cambios del check de editornotificaciones | 3 |
| `.claude/tests/test_rules.py` | Reglas contra el motor real de producción | 3 |
| `.claude/agents/agent-dotnet-api.md` | Ejecutor del perfil, sin contenido de la 001 | 4 |
| `.claude/skills/speckit-a-harness/verificar_traduccion.py` | Check determinista de la traducción | 5 |
| `.claude/tests/test_verificar_traduccion.py` | Pruebas del verificador | 5 |
| `.claude/skills/speckit-a-harness/SKILL.md` | Apertura del ticket: `tasks.md` → `plan.json` + `plan.md` | 6 |
| `.claude/commands/ticket-abrir-sdd.md` | `/ticket-abrir-sdd <carpeta de la feature>` | 6 |
| `specs/001-cuentas-bancarias/tasks.md`, `mis_notas/tasks-notas.md` | Salida de `/speckit-tasks` y la nota de la fase | 7 |
| `.harness/tickets/SSD-001/*` (ignorado) | Ticket abierto y plan validado | 8 |
| `docs/puente-speckit-harness.md`, `docs/candidatas-a-produccion.md`, `mis_notas/plan-notas.md` | Documentación | 9 |

Las pruebas Python viven en `.claude/tests/` y no en `.claude/checks/`, porque el harness carga como check todo `*.py` de esa carpeta. Se corren con `python -m unittest discover -s .claude/tests -v`.

---

### Task 1: Commit de los artefactos de plan y enmienda de la constitución a v1.1.0

**Files:**
- Modify: `.specify/memory/constitution.md:39,41,53`
- Modify: `specs/001-cuentas-bancarias/plan.md:45,55`

**Interfaces:** ninguna.

- [ ] **Step 1: Commit de lo pendiente de la sesión anterior, antes de editar**

```bash
git add specs/001-cuentas-bancarias/plan.md specs/001-cuentas-bancarias/research.md \
        specs/001-cuentas-bancarias/data-model.md specs/001-cuentas-bancarias/quickstart.md \
        specs/001-cuentas-bancarias/contracts/ mis_notas/clarify-notas.md mis_notas/plan-notas.md \
        docs/superpowers/
git commit -m "spec(001): add implementation plan and spec-kit to harness bridge design"
```

- [ ] **Step 2: Enmendar la sección "Flujo de trabajo" y la línea de versión**

- Línea 39 → `- El flujo es obligatorio: specify, clarify, plan y tasks con Spec Kit; la ejecución, fase por fase, bajo el harness.`
- Línea 41 → `- Cada fase del harness se cierra con un commit propio al ser aprobada.`
- Línea 53 → `**Version**: 1.1.0 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-27`
- La línea 40 (Constitution Check antes de escribir código) no cambia.

- [ ] **Step 3: Actualizar a mano el Constitution Check de `plan.md`**

No se vuelve a correr `/speckit-plan`.

- Línea 45 → `Constitución v1.0.0; la fila «Flujo de trabajo» se re-verificó contra v1.1.0.`
- Fila 55 → `| **Flujo de trabajo** | El plan pasa el Constitution Check antes de escribir código. La ejecución va fase por fase bajo el harness, con un commit por fase aprobada (re-verificado contra v1.1.0). | ✅ PASS |`

- [ ] **Step 4: Verificar**

Run: `grep -n "1.1.0\|commit propio\|bajo el harness" .specify/memory/constitution.md specs/001-cuentas-bancarias/plan.md`
Expected: aparecen las cuatro líneas nuevas y ninguna menciona ya "implement" ni "Cada tarea de tasks.md".

- [ ] **Step 5: Commit**

```bash
git add .specify/memory/constitution.md specs/001-cuentas-bancarias/plan.md
git commit -m "docs: amend constitution to v1.1.0 (execution under the harness, commit per phase)"
```

---

### Task 2: `.gitignore`

**Files:**
- Create: `.gitignore`

**Interfaces:** ninguna.

- [ ] **Step 1: Crear `.gitignore`** con estas líneas: `.harness/`, `bin/`, `obj/`, `*.db`, `*.db-*`, `TestResults/` y `__pycache__/`. Las dos últimas entradas no están en la lista del diseño: `*.db-*` cubre los archivos auxiliares de SQLite, y `__pycache__/` cubre los `.pyc` que dejan los checks y las pruebas Python, que `run-checks` tomaría como archivos sin rastrear.

- [ ] **Step 2: Verificar**

Run: `git check-ignore -v .harness/x bin/x src/A/obj/x cuentas.db cuentas.db-journal tests/T/TestResults/x .claude/tests/__pycache__/x.pyc; git check-ignore specs/001-cuentas-bancarias/spec.md; echo "exit=$?"`
Expected: las siete primeras rutas muestran su regla, y la última termina con `exit=1`, porque `spec.md` no se ignora.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore harness state and build outputs"
```

---

### Task 3: Perfil — `rules.json` y check `dotnet_build`

**Files:**
- Create: `.claude/rules.json`
- Create: `.claude/checks/dotnet_build.py` (copia)
- Test: `.claude/tests/test_rules.py`

**Interfaces:**
- Consumes: `check_prohibited(rel_path: str, agregadas: list[tuple[int, str]], rules: dict) -> list[dict]` de `~/.claude/hooks/lib/checks.py` (producción, solo se importa). `resolve_check_names(nombres, rules) -> (resueltos, desconocidos)` de `~/.claude/hooks/lib/contracts.py`.
- Produces: perfil `ssd01`; reglas `no_secretos`, `dep_nueva`, `solo_dos_endpoints`; grupo `constitucion` = las tres; check estructural `dotnet_build`. Task 6 usa `checks_deterministas: ["dotnet_build", "constitucion"]`.

- [ ] **Step 1: Escribir las pruebas que fallan** en `.claude/tests/test_rules.py`

Hacen `sys.path.insert(0, str(Path.home() / ".claude" / "hooks"))` y luego `from lib.checks import check_prohibited` y `from lib.contracts import resolve_check_names`. Cargan `RAIZ / ".claude" / "rules.json"`, con `RAIZ = Path(__file__).resolve().parents[2]`. Helper: `ids(ruta, linea) = {h["id"] for h in check_prohibited(ruta, [(1, linea)], reglas)}`.

```python
API = "src/CuentasBancarias.Api/"
def test_positivos_no_secretos(self):
    for ruta, linea in [(API + "Program.cs", 'options.ApiKey = "abc123";'),
                        (API + "appsettings.json", '"ApiKey": "clave-real"'),
                        (API + "appsettings.Development.json", '"Password": "x1"')]:
        self.assertIn("no_secretos", ids(ruta, linea), linea)
def test_negativos_no_secretos(self):
    for linea in ['var clave = builder.Configuration["Auth:ApiKey"];',
                  '"ApiKey": ""', 'const string Header = "X-Api-Key";']:
        self.assertNotIn("no_secretos", ids(API + "Program.cs", linea), linea)
        self.assertNotIn("no_secretos", ids(API + "appsettings.json", linea), linea)
def test_positivos_solo_dos_endpoints(self):
    for linea in ['app.MapDelete("/cuentas/{id}", h);', 'app.MapPut("/cuentas/{id}", h);',
                  'app.MapPatch("/cuentas/{id}", h);', 'app.MapGet("/health", h);',
                  'app.MapPost("/transferencias", h);', 'app.MapGet("/cuentasx", h);',
                  'app.MapMethods("/cuentas", new[] { "HEAD" }, h);']:
        self.assertIn("solo_dos_endpoints", ids(API + "Program.cs", linea), linea)
def test_negativos_solo_dos_endpoints(self):
    for linea in ['app.MapPost("/cuentas", h);', 'app.MapGet("/cuentas/{id}", h);']:
        self.assertNotIn("solo_dos_endpoints", ids(API + "Program.cs", linea), linea)
def test_dep_nueva_es_warning(self):
    hallazgos = check_prohibited("src/X/X.csproj",
        [(1, '<PackageReference Include="Dapper" Version="2.1.35" />')], reglas)
    self.assertEqual([(h["id"], h["severidad"]) for h in hallazgos], [("dep_nueva", "warning")])
def test_severidades(self):
    severidad = {r["id"]: r["severidad"] for r in reglas["prohibido"]}
    self.assertEqual(severidad, {"no_secretos": "error", "dep_nueva": "warning",
                                 "solo_dos_endpoints": "error"})
def test_motor_respeta_excluir(self):
    linea = 'options.ApiKey = "clave-de-prueba";'
    self.assertEqual(ids("tests/CuentasBancarias.Tests/ApiFactory.cs", linea), set())
    self.assertEqual(ids(".claude/rules.json", '"ApiKey": "clave-real"'), set())
    self.assertEqual(ids("specs/001-x/contracts/ejemplo.json", '"ApiKey": "k1"'), set())
    self.assertEqual(ids("tests/CuentasBancarias.Tests/RutasTests.cs", 'app.MapDelete("/x", h);'), set())
def test_grupos_y_checks_resuelven(self):
    resueltos, desconocidos = resolve_check_names(["dotnet_build", "constitucion"], reglas)
    self.assertEqual(desconocidos, [])
    self.assertEqual(set(resueltos), {"dotnet_build", "no_secretos", "dep_nueva", "solo_dos_endpoints"})
    self.assertEqual(reglas["perfil"], "ssd01")
    self.assertIs(reglas["audit_comments"]["requerido"], False)
def test_dotnet_build_es_copia_exacta(self):
    produccion = Path("C:/AZZULE/IA harness/profiles/editornotificaciones/checks/dotnet_build.py")
    self.assertEqual((RAIZ / ".claude/checks/dotnet_build.py").read_bytes(), produccion.read_bytes())
```

- [ ] **Step 2: Verificar que fallan**

Run: `python -m unittest discover -s .claude/tests -v`
Expected: ERROR, con `FileNotFoundError` de `.claude/rules.json`.

- [ ] **Step 3: Crear `.claude/rules.json`**

Usa el formato de `C:\AZZULE\IA harness\profiles\editornotificaciones\rules.json`:

- `"perfil": "ssd01"`.
- `audit_comments`: `{requerido: false, severidad: "warning", nota: "Repo nuevo con historial git: no usa los bloques [B]/[E]"}`.
- `prohibido` con estas tres reglas:
  - `no_secretos`: `archivos [".cs", ".json"]`, `excluir ["tests/", ".claude/", "specs/"]`, `error`, Principio IV. Patrón de partida: `(?i)\b(api[-_]?key|password|pwd|secret)"?\s*[:=]\s*@?"[^"\s]+"`.
  - `dep_nueva`: `archivos [".csproj"]`, `warning`, patrón `<PackageReference\s`. Mensaje: el escéptico la contrasta con la lista justificada en `plan.md` (Principio III).
  - `solo_dos_endpoints`: `archivos [".cs"]`, `excluir ["tests/"]`, `error`, patrón `\bMap(Put|Delete|Patch|Methods)\s*\(|\bMap(Get|Post)\s*\(\s*"(?!/cuentas(/|"))`, restricción de alcance.
- Los mensajes van en español y citan el principio.
- `checks_estructurales: ["dotnet_build"]`.
- `grupos: {"constitucion": [las tres]}`.
- Sin `no_new_deps`: el diseño explica por qué.

- [ ] **Step 4: Copiar el check**

```bash
mkdir -p .claude/checks && cp "/c/AZZULE/IA harness/profiles/editornotificaciones/checks/dotnet_build.py" .claude/checks/
```

- [ ] **Step 5: Verificar que pasan**

Run: `python -m unittest discover -s .claude/tests -v`
Expected: todas OK. Si un patrón falla, se ajusta el patrón, nunca la prueba.

- [ ] **Step 6: Commit**

```bash
git add .claude/rules.json .claude/checks/dotnet_build.py .claude/tests/test_rules.py
git commit -m "feat(harness): add ssd01 profile rules and dotnet_build check"
```

---

### Task 4: Agente ejecutor `agent-dotnet-api`

**Files:**
- Create: `.claude/agents/agent-dotnet-api.md`

**Interfaces:**
- Produces: el agente `agent-dotnet-api`. `harness.list_agents` toma el nombre del archivo, y el `agente_ejecutor` de Task 6 lo usa.

- [ ] **Step 1: Escribir el agente**

Toma la forma de `C:\AZZULE\IA harness\profiles\editornotificaciones\agents\agent-notif-api.md`: frontmatter `name`, `description` y `model: opus`, más secciones numeradas. Debe contener, en este orden:

1. **Stack**: .NET 10 (SDK 10.0.x), ASP.NET Core Web API, SQLite y xUnit. La solución `.slnx` va en la raíz del repo, porque `dotnet_build` la busca ahí. Los paquetes que trae la plantilla de xUnit forman parte del stack. Cualquier otro paquete tiene que estar justificado en el `plan.md` de la feature.
2. **Cómo está organizada una feature de spec-kit**: `specs/<feature>/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` y `tasks.md`. La regla es **leer solo los `anclajes` de la fase**: `ruta#ancla` apunta a un FR, a una sección `R#`, a un encabezado o a una ruta del contrato. Si un anclaje no alcanza, el agente lo dice en `resultado.md` en lugar de leer la spec completa.
3. **Test-first**:
   - primero escribe las pruebas de la fase;
   - corre `dotnet test` y pega la salida en rojo en `intento_N/resultado.md`, bajo `## Rojo`;
   - después implementa hasta verde y pega la salida bajo `## Verde`.
   - En una fase sin pruebas, la sección `## Rojo` dice "no aplica" y explica por qué.
4. **Guardrails** (`rules.json` en prosa):
   - `no_secretos`: los secretos se leen de configuración (`Auth:ApiKey` por user-secrets o variable de entorno), nunca se escriben como literal. Las pruebas sí pueden usar una clave literal.
   - `solo_dos_endpoints`: solo hay crear y consultar bajo `/cuentas`, y cualquier otra operación requiere enmienda a la constitución. Viene de la constitución del repo, no de la feature, por eso sí va en el agente.
   - `dep_nueva`: un paquete que no está justificado en `plan.md` se detiene y se pregunta.
5. **Operación bajo el harness**:
   - recibe la fase, `ticket_context.json`, `herramientas_permitidas` y el `historial_fallos` completo si `intento_actual > 1`;
   - el hook `PostToolUse` es autocorrección, no un reintento;
   - **nunca hace `git commit`**, porque el harness compara contra `HEAD` y el commit lo hace el humano al aprobar;
   - `resultado.md` lleva qué hizo, archivos, comandos con su salida y lo que no pudo verificar.

- [ ] **Step 2: Verificar que no lleva contenido de la 001 y que tiene lo exigido**

Run: `grep -n -i "001\|cuentas-bancarias\|Ana Pérez\|CuentaStore" .claude/agents/agent-dotnet-api.md; echo "exit=$?"; grep -c "## Rojo\|anclajes\|git commit\|historial_fallos\|slnx" .claude/agents/agent-dotnet-api.md`
Expected: el primer grep no encuentra nada (`exit=1`) y el conteo da 5 o más.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/agent-dotnet-api.md
git commit -m "feat(harness): add agent-dotnet-api executor"
```

---

### Task 5: `verificar_traduccion.py`

**Files:**
- Create: `.claude/skills/speckit-a-harness/verificar_traduccion.py`
- Test: `.claude/tests/test_verificar_traduccion.py`

**Interfaces:**
- Produces:
  - `verificar(carpeta_feature: Path, plan: dict) -> list[str]`: lista de errores; si está vacía, la traducción es válida.
  - `main(argv: list[str]) -> int`, con uso `python verificar_traduccion.py <carpeta_feature> <plan.json>`.
    - Exit 0: imprime `traducción: OK (<n> tareas, <m> FR, <k> fases)`.
    - Exit 1: imprime un error por línea.
    - Exit 2: uso incorrecto o archivo inexistente.
  - La constante `FRASE_TEST_FIRST` (ver Global Constraints).
  - El campo opcional de `plan.json` en el nivel superior `fuera_de_ejecucion: [{"ref": "FR-xxx", "motivo": "<no vacío>"}]`. `validate_plan` de producción ignora claves extra.

**Reglas de reconocimiento** (lo que el diseño deja al constructor):

| Qué | Cómo se reconoce |
|---|---|
| Fase de `tasks.md` | `^##\s+(Phase\|Fase)\s+\d+\s*:\s*(.+)$` (case-insensitive). El título es el grupo 2. |
| Fase de historia | El título coincide con `(User Story\|Historia de usuario)\s+(\d+)` (case-insensitive) |
| Tarea | `^\s*-\s*\[[ xX]\]\s*(T\d{3})\b` |
| Tarea de prueba | Está bajo un `###` que empieza por `Tests` o `Pruebas`, o su línea contiene `tests/\S*Tests?\.cs` |
| FR definido | `\*\*(FR-\d{3}[a-z]?)\*\*` en `spec.md` |
| FR anclado | El `ref` de un anclaje termina en `spec.md#(FR-\d{3}[a-z]?)`, con coincidencia exacta del id |
| Independent Test | En `spec.md`, bajo `### User Story N`, el texto desde `**Independent Test**:` hasta la primera línea en blanco |
| Paso que traduce una tarea | El paso **empieza** por `T\d{3}`. Una mención en medio del texto, como "depends on T012", no cuenta. |
| Comparación literal | Ambos textos se normalizan con `" ".join(s.split())` antes de buscar uno dentro del otro |

**Mensajes de error** (las pruebas buscan estos fragmentos):

- `tasks.md: no se reconoce ninguna fase con tareas`
- `<T>: no aparece en ningún paso`
- `<T>: aparece en más de una fase (<fase_a>, <fase_b>)`
- `<fase>: el paso '<T>' no es una tarea de tasks.md`
- `<fase>: no traduce ninguna fase de tasks.md`
- `<fase>: mezcla tareas de varias fases de tasks.md`
- `<FR>: no está anclado en ninguna fase ni en fuera_de_ejecucion`
- `fuera_de_ejecucion[<i>]: requiere ref FR-xxx y motivo no vacío`
- `spec.md: User Story <n> no tiene Independent Test`
- `<fase>: criterio_exito no contiene literal el Independent Test de User Story <n>`
- `<fase>: tiene pruebas y criterio_exito no trae la frase de evidencia test-first`
- `<fase>: prueba_manual.requerida debe ser true (decisión 8)`

- [ ] **Step 1: Escribir las pruebas que fallan** en `.claude/tests/test_verificar_traduccion.py`

`setUp` escribe `SPEC` y `TASKS` en un `tempfile.TemporaryDirectory()`. El módulo se importa con `sys.path.insert(0, str(RAIZ / ".claude/skills/speckit-a-harness"))`. Fixture:

```python
SPEC = """### User Story 1 - Crear (Priority: P1)

**Independent Test**: Se prueba creando
una cuenta válida.

### User Story 2 - Consultar (Priority: P1)

**Independent Test**: Se prueba sembrando una cuenta.

- **FR-001**: crear.
- **FR-002**: validar.
- **FR-002a**: recortar.
- **FR-013**: MUST NOT listar.
"""
TASKS = """## Phase 1: Setup
- [ ] T001 Crear solución en CuentasBancarias.slnx
## Phase 2: Foundational
- [ ] T002 Middleware en src/Api/Auth.cs
## Phase 3: User Story 1 - Crear (Priority: P1)
### Tests for User Story 1
- [ ] T003 [US1] Pruebas en tests/T/CrearCuentaTests.cs
- [ ] T004 [US1] Endpoint en src/Api/Program.cs (depends on T002)
## Phase 4: User Story 2 - Consultar (Priority: P1)
- [ ] T005 [US2] Endpoint en src/Api/Program.cs
## Phase 5: Polish
- [ ] T006 README
"""
```

`plan_valido()` devuelve 5 fases (`fase_1`…`fase_5`). Cada una tiene sus pasos (`"T001 Crear solución…"`, etc., y al final el paso fijo `ESCRIBE intento_N/resultado.md…`), `prueba_manual: {"requerida": True}` y anclajes a `specs/x/spec.md#FR-001` (fase_3), `#FR-002` y `#FR-002a` (fase_3) y `#FR-013` (fase_4). El `criterio_exito` de fase_3 es `"Se prueba creando una cuenta válida. " + FRASE_TEST_FIRST`, y el de fase_4 es `"Se prueba sembrando una cuenta."`.

Pruebas. Cada una modifica una sola cosa de `plan_valido()` y comprueba con `assertTrue(any(frag in e for e in errores))`:

| Prueba | Cambio | Esperado |
|---|---|---|
| `test_plan_valido` | ninguno | `verificar(...) == []` |
| `test_tarea_ausente` | se quita el paso T006 | `T006: no aparece en ningún paso` |
| `test_tarea_en_dos_fases` | se agrega el paso T002 a fase_3 | `T002: aparece en más de una fase` |
| `test_paso_que_menciona_otra_tarea_no_cuenta` | ninguno: T004 menciona "depends on T002" en fase_3 | `[]` |
| `test_tarea_inventada` | se agrega el paso T099 a fase_5 | `fase_5: el paso 'T099' no es una tarea` |
| `test_fase_que_mezcla` | se juntan fase_1 y fase_2 en una sola | `mezcla tareas de varias fases` |
| `test_fase_sin_tareas` | se agrega fase_6, solo con el paso fijo | `fase_6: no traduce ninguna fase` |
| `test_fr_sin_anclar` | se quita el anclaje FR-013 | `FR-013: no está anclado` |
| `test_fr_fuera_de_ejecucion_con_motivo` | sin FR-013, `fuera_de_ejecucion=[{"ref":"FR-013","motivo":"negativo"}]` | `[]` |
| `test_fr_fuera_de_ejecucion_sin_motivo` | el mismo, con `motivo: ""` | `fuera_de_ejecucion[0]: requiere ref` |
| `test_fr_con_sufijo_no_cubre_el_base` | se quita el anclaje FR-002 y queda FR-002a | `FR-002: no está anclado` |
| `test_criterio_sin_independent_test` | criterio de fase_3 = solo `FRASE_TEST_FIRST` | `fase_3: criterio_exito no contiene literal el Independent Test de User Story 1` |
| `test_independent_test_con_otro_salto_de_linea` | criterio de fase_3 con `"Se prueba\ncreando una  cuenta válida."` | `[]` |
| `test_fase_con_pruebas_sin_frase` | se quita `FRASE_TEST_FIRST` de fase_3 | `fase_3: tiene pruebas` |
| `test_fase_sin_pruebas_no_exige_frase` | ninguno (fase_4 no trae la frase) | `[]` |
| `test_prueba_manual_no_requerida` | fase_1 con `requerida: False` | `fase_1: prueba_manual.requerida debe ser true` |
| `test_tasks_sin_fases` | `tasks.md` = `"# Tasks\n"` | `tasks.md: no se reconoce ninguna fase` |
| `test_tareas_marcadas_x` | `tasks.md` con `- [x]` en T001–T003 | `[]` |
| `test_titulos_en_espanol` | `## Fase 3: Historia de usuario 1 - Crear` y `### Pruebas de la historia 1` | `[]` |
| `test_main_codigos_de_salida` | `main([carpeta, plan.json válido])` | `0` e imprime `traducción: OK (6 tareas, 4 FR, 5 fases)` |
| | con un plan inválido | `1` |
| | `main([])` | `2` |

- [ ] **Step 2: Verificar que fallan**

Run: `python -m unittest .claude/tests/test_verificar_traduccion.py -v` (desde la raíz; si `unittest` no acepta la ruta, usar `discover -s .claude/tests -p "test_verificar*"`)
Expected: ERROR, `ModuleNotFoundError: verificar_traduccion`.

- [ ] **Step 3: Implementar `verificar_traduccion.py`**

Lleva un docstring de módulo en el estilo de `dotnet_build.py` (qué verifica y por qué es la forma barata de verificar el juicio del modelo). Usa las funciones privadas `_fases_tasks(texto) -> list[dict]` (`titulo`, `historia: int | None`, `tareas: list[str]`, `con_pruebas: bool`), `_independent_tests(spec) -> dict[int, str]` y `_frs(spec) -> list[str]`, y aplica las reglas de las tablas de arriba. Corrige la codificación de stdout con `reconfigure(encoding="utf-8")`, igual que los hooks de producción.

- [ ] **Step 4: Verificar que pasan**

Run: `python -m unittest discover -s .claude/tests -v`
Expected: todas OK, incluidas las de Task 3.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/speckit-a-harness/verificar_traduccion.py .claude/tests/test_verificar_traduccion.py
git commit -m "feat(harness): add deterministic check for tasks.md to plan.json translation"
```

---

### Task 6: Skill `speckit-a-harness` y comando `/ticket-abrir-sdd`

**Files:**
- Create: `.claude/skills/speckit-a-harness/SKILL.md`
- Create: `.claude/commands/ticket-abrir-sdd.md`

**Interfaces:**
- Consumes: `verificar_traduccion.py` (Task 5), el grupo `constitucion` y `dotnet_build` (Task 3), y `agent-dotnet-api` (Task 4).
- Produces: `.harness/tickets/<id>/ticket.md`, `plan.json` y `plan.md`. El ciclo de producción (`/fase`) los lee de ahí.

- [ ] **Step 1: Escribir `SKILL.md`**

Frontmatter:
- `name: speckit-a-harness`
- `description`: abre un ticket del harness a partir de una feature de spec-kit con `tasks.md` terminado, y traduce `tasks.md` a `plan.json` en lugar de usar task-planner. Se usa con `/ticket-abrir-sdd`.

Cuerpo, en el estilo imperativo de `~/.claude/skills/ticket-loop/SKILL.md`:

- Línea `CLI = …`.
- Los pasos 0–7 del diseño §2, literales en su contenido. El paso 4 lleva `--perfil ssd01`, y el paso 6 lleva los dos comandos exactos:
  - `python .claude/skills/speckit-a-harness/verificar_traduccion.py <carpeta> .harness/tickets/<id>/plan.json`
  - `CLI validate --contrato plan --archivo .harness/tickets/<id>/plan.json`
- La tabla de traducción completa del diseño. Cambios respecto al diseño:
  - `checks_deterministas` queda en `["dotnet_build", "constitucion"]`.
  - `herramientas_permitidas` queda en `["Read", "Grep", "Glob", "Edit", "Write", "Bash(dotnet *)"]`.
  - `FRASE_TEST_FIRST` va literal.
  - El campo `fuera_de_ejecucion` se usa solo para FR que ninguna tarea implementa, con motivo.
- El formato de `plan.md` del diseño (tabla de fases: tareas, `depende_de`, prueba manual, enlace a `tasks.md`).
- Una sección final "Lo que no hace", con tres puntos:
  - no reescribe ni re-planifica tareas (anti-objetivo "planificar dos veces");
  - no abre fases;
  - no copia contenido de la spec a `ticket.md`.

- [ ] **Step 2: Escribir el comando** con la forma de `C:\AZZULE\IA harness\harness\commands\ticket-abrir.md`

```markdown
---
description: Abre un ticket del harness desde una feature de spec-kit con tasks.md
argument-hint: [carpeta de la feature, p. ej. specs/NNN-mi-feature]
---

Usa la skill `speckit-a-harness`. Carpeta de la feature: `$ARGUMENTS`

Si no viene carpeta, pídela antes de hacer nada. No inventes el id de ticket, el
desarrollador ni la fecha: pregúntalos una sola vez.
```

- [ ] **Step 3: Verificar**

Run: `grep -c "verificar_traduccion.py\|validate --contrato plan\|hallazgos-pendientes\|Evidencia test-first\|requerida" .claude/skills/speckit-a-harness/SKILL.md; grep -n -i "001\|cuentas" .claude/skills/speckit-a-harness/SKILL.md .claude/commands/ticket-abrir-sdd.md; echo "exit=$?"`
Expected: el conteo da 5 o más, y el segundo grep no encuentra nada (`exit=1`).

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/speckit-a-harness/SKILL.md .claude/commands/ticket-abrir-sdd.md
git commit -m "feat(harness): add speckit-a-harness skill and /ticket-abrir-sdd command"
```

---

### Task 7: `/speckit-tasks` con trazabilidad

Esta tarea es interactiva y corre en la sesión principal, no en un subagente.

**Files:**
- Create: `specs/001-cuentas-bancarias/tasks.md` (lo genera el skill)
- Create: `mis_notas/tasks-notas.md`

**Interfaces:**
- Produces: un `tasks.md` cuyas tareas citan FR, R# y rutas del contrato. Task 8 lo traduce.

- [ ] **Step 1: Correr el skill** `speckit-tasks` con el argumento literal: `cada tarea cita entre paréntesis los FR, las decisiones de research (R#) y las rutas del contrato que implementa`

- [ ] **Step 2: Verificar la trazabilidad y la forma**

Run: `grep -cE "^\s*- \[ \] T[0-9]{3}" specs/001-cuentas-bancarias/tasks.md; grep -E "^\s*- \[ \] T[0-9]{3}" specs/001-cuentas-bancarias/tasks.md | grep -vcE "FR-[0-9]{3}|R[1-8]|/cuentas"; grep -nE "^## (Phase|Fase)" specs/001-cuentas-bancarias/tasks.md`
Expected:
- Se cuentan N tareas.
- Las tareas sin cita son solo de Setup o Polish (se revisan a ojo).
- Hay unas 5 fases: Setup, Foundational, US1, US2 y Polish.
- Si los encabezados no siguen `## Phase N:` o `## Fase N:`, se corrige `tasks.md` a mano o se vuelve a correr el skill. **No** se afloja el verificador.

- [ ] **Step 3: Escribir `mis_notas/tasks-notas.md`** en el estilo de `mis_notas/clarify-notas.md`, con cuatro partes:
  - qué es el paso tasks;
  - qué hizo el skill;
  - el argumento de trazabilidad y por qué existe (los anclajes del puente);
  - lo que salió: número de fases y tareas, y si alguna tarea quedó sin cita.

- [ ] **Step 4: Commit**

```bash
git add specs/001-cuentas-bancarias/tasks.md mis_notas/tasks-notas.md
git commit -m "spec(001): add traceable tasks"
```

---

### Task 8: Abrir el ticket `SSD-001`

Esta tarea es interactiva y corre en la sesión principal.

**Files:** solo bajo `.harness/`, que está ignorado. No hay commit.

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: el ticket activo `SSD-001`, con `plan.json` válido y `plan.md`.

- [ ] **Step 1: Correr** `/ticket-abrir-sdd specs/001-cuentas-bancarias` y responder las preguntas: id `SSD-001`, número de ticket, desarrollador y fecha `DD-MM-YYYY`.

- [ ] **Step 2: Verificar por separado lo que el skill dice que verificó**

Run: `python .claude/skills/speckit-a-harness/verificar_traduccion.py specs/001-cuentas-bancarias .harness/tickets/SSD-001/plan.json && python "$HOME/.claude/hooks/cli.py" validate --contrato plan --archivo .harness/tickets/SSD-001/plan.json`
Expected: `traducción: OK (...)` y `plan: válido`.

- [ ] **Step 3: Revisar a ojo `plan.md`** con el desarrollador.
  - Una fase por cada fase de `tasks.md`.
  - Todas con prueba manual.
  - `depende_de` coincide con "Dependencies & Execution Order".
  - Si `plan.json` usa `fuera_de_ejecucion`, el desarrollador ve el motivo.

- [ ] **Step 4: Verificar que el árbol de trabajo está limpio**

Run: `git status --porcelain`
Expected: sin salida. Nada de `.harness/` aparece.

---

### Task 9: Documentación del puente

**Files:**
- Create: `docs/puente-speckit-harness.md`
- Create: `docs/candidatas-a-produccion.md`
- Modify: `mis_notas/plan-notas.md:81` (la línea "Pendiente: diseñar y construir el puente.")

**Interfaces:** ninguna.

- [ ] **Step 1: `docs/puente-speckit-harness.md`**: cómo se usa el puente de punta a punta en la siguiente feature.
  - Prerrequisitos: el perfil y `.gitignore`.
  - specify → clarify → plan → `/speckit-tasks` con el argumento de trazabilidad.
  - Commit de todo.
  - `/ticket-abrir-sdd`.
  - `/fase fase_N`, `/fase-ok` o `/fase-fallo`, y `/hallazgo-*`.
  - Commit `feat(<feature>): fase_N <título>` al aprobar, con los `[x]` de `tasks.md` y `.claude/biblioteca/`.
  - Qué hacer con cada lección según su `componente` (decisión 9).
  - Ejemplos con la 001.

- [ ] **Step 2: `docs/candidatas-a-produccion.md`**: un encabezado, un párrafo que explica la decisión 9 y una tabla vacía con las columnas `Ref (TICKET/fase_N/hN)`, `Pieza de producción`, `Lección`, `Evidencia` y `Estado`.

- [ ] **Step 3: `mis_notas/plan-notas.md`**: reemplazar la línea "Pendiente" por una lista corta de lo construido, con enlaces a `docs/puente-speckit-harness.md` y al diseño. La nota de aprendizaje con los hallazgos se escribe al terminar la ejecución, no ahora.

- [ ] **Step 4: Commit y comprobación final**

```bash
git add docs/puente-speckit-harness.md docs/candidatas-a-produccion.md mis_notas/plan-notas.md
git commit -m "docs: document the spec-kit to harness bridge"
git status --porcelain
```
Expected: `git status` sin salida. El repo queda listo para `/fase fase_1`.

---

## Después de este plan (fuera de él)

- Ejecución fase por fase con el ciclo de producción, con gate humano y un commit por fase aprobada (`feat(001): fase_N <título>`).
- Al cerrar cada fase, las lecciones van al repo o a `docs/candidatas-a-produccion.md`.
- Al terminar, una nota nueva en `mis_notas/` con lo aprendido.
