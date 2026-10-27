---

description: "Task list for feature 001-cuentas-bancarias"
---

# Tasks: Cuentas Bancarias

**Input**: Design documents from `/specs/001-cuentas-bancarias/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Requeridas. FR-011 y el Principio II de la constitución exigen pruebas de integración escritas **antes** de la implementación y fallando. Toda fase con pruebas las escribe primero.

**Organization**: Las tareas se agrupan por historia de usuario. Cada tarea cita entre paréntesis los FR, las decisiones de research (R#) y las rutas del contrato (`contracts/openapi.yaml`) que implementa.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: Historia de usuario de la tarea (US1, US2)
- Rutas relativas a la raíz del repo, según la estructura de `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Solución, proyectos y dependencias justificadas en `plan.md`, compilando.

- [ ] T001 Crear la solución `CuentasBancarias.slnx` en la raíz y el proyecto Minimal API `src/CuentasBancarias.Api/CuentasBancarias.Api.csproj` con `dotnet new web` (net10.0, `Nullable` e `ImplicitUsings` habilitados), sin controladores, OpenAPI ni Swagger; quitar el `app.MapGet("/", …)` que trae la plantilla en `src/CuentasBancarias.Api/Program.cs` y correr `dotnet user-secrets init --project src/CuentasBancarias.Api` para que el `.csproj` tenga `UserSecretsId` (R1, R3)
- [ ] T002 Crear el proyecto xUnit `tests/CuentasBancarias.Api.Tests/CuentasBancarias.Api.Tests.csproj` con referencia a `src/CuentasBancarias.Api`, agregarlo a `CuentasBancarias.slnx` y borrar el `UnitTest1.cs` de la plantilla (R8)
- [ ] T003 Agregar `Microsoft.Data.Sqlite` a `src/CuentasBancarias.Api/CuentasBancarias.Api.csproj` y `Microsoft.AspNetCore.Mvc.Testing` a `tests/CuentasBancarias.Api.Tests/CuentasBancarias.Api.Tests.csproj`; ningún otro paquete (R4, R8)
- [ ] T004 [P] Dejar `src/CuentasBancarias.Api/appsettings.json` con `ConnectionStrings:Cuentas = "Data Source=cuentas.db"` y **sin** la sección `Auth` (R3, R4)

**Checkpoint**: `dotnet build CuentasBancarias.slnx` compila sin errores y `dotnet test` corre sin fallos.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Credencial obligatoria antes de cualquier endpoint, almacenamiento SQLite y factory de pruebas. Ambas historias dependen de esta fase.

**⚠️ CRITICAL**: Ninguna historia empieza hasta que esta fase esté completa.

### Tests for Foundational ⚠️

> **NOTE: Escribir estas pruebas PRIMERO y comprobar que FALLAN antes de implementar**

- [ ] T005 Crear `tests/CuentasBancarias.Api.Tests/ApiFactory.cs`: `WebApplicationFactory<Program>` con un archivo SQLite temporal único por instancia y una API key de prueba inyectada por configuración; expone un cliente con credencial, un cliente sin ella, la ruta del archivo SQLite y un helper `SembrarCuenta(Guid id, string titular, long saldoCentavos)` que inserta con un `SqliteConnection` propio; al liberarse llama a `SqliteConnection.ClearAllPools()` y borra el archivo (FR-012; R4, R8)
- [ ] T006 Escribir `tests/CuentasBancarias.Api.Tests/AutenticacionTests.cs`: una ruta cualquiera sin header `X-Api-Key`, con el header vacío y con un valor incorrecto responde `401` con cuerpo vacío e idéntico en los tres casos; un `POST /cuentas` sin credencial y con JSON mal formado responde `401`, no `400`; la app no arranca si `Auth:ApiKey` falta o está vacía (FR-009, FR-010; R3; `#/components/securitySchemes/ApiKey`, `#/components/responses/NoAutorizado`)

### Implementation for Foundational

- [ ] T007 [P] Crear `src/CuentasBancarias.Api/Cuentas/Cuenta.cs` con `record Cuenta(Guid Id, string Titular, decimal Saldo)` (data-model: Entidad Cuenta)
- [ ] T008 Crear `src/CuentasBancarias.Api/Cuentas/CuentaStore.cs`: clase concreta sin interfaz con `CrearEsquema()` (`CREATE TABLE IF NOT EXISTS Cuentas`, data-model: Esquema SQLite), `Insertar(Cuenta)` y `Obtener(Guid) -> Cuenta?`; `Id` como `TEXT` formato `D` en minúsculas y saldo como `SaldoCentavos INTEGER` (`saldo * 100` al guardar, `/ 100m` al leer); connection string `ConnectionStrings:Cuentas` (FR-006; R4, R5, R6)
- [ ] T009 Crear `src/CuentasBancarias.Api/Auth/ApiKeyMiddleware.cs`: lee `X-Api-Key`, lo compara con `Auth:ApiKey` con `CryptographicOperations.FixedTimeEquals` sobre UTF-8 y, si no coincide (ausente, vacío o incorrecto), responde `401` sin cuerpo ni `WWW-Authenticate` y sin llamar al siguiente paso (FR-009, FR-010; R3; `#/components/securitySchemes/ApiKey`)
- [ ] T010 Escribir `src/CuentasBancarias.Api/Program.cs`: falla al arrancar si `Auth:ApiKey` falta o está vacía; `AddProblemDetails()`; registra `CuentaStore` y llama a `CrearEsquema()` al iniciar; `app.UseMiddleware<ApiKeyMiddleware>()` antes de mapear endpoints; llama a `app.MapCuentasEndpoints()` de `src/CuentasBancarias.Api/Cuentas/CuentasEndpoints.cs` (que en esta fase existe sin rutas) y no mapea ninguna otra ruta; termina con `public partial class Program;` (FR-009, FR-010, FR-013; R3, R4, R7, R8)

**Checkpoint**: Toda petición sin credencial válida responde `401` sin cuerpo, antes de leer el cuerpo, y la API no arranca sin `Auth:ApiKey`.

---

## Phase 3: User Story 1 - Crear cuenta bancaria (Priority: P1) 🎯 MVP

**Goal**: Un cliente autorizado crea una cuenta con titular y saldo inicial y recibe la cuenta con su identificador.

**Independent Test**: Se prueba enviando una petición de creación con datos válidos y verificando que la respuesta contiene un identificador único y los datos enviados. No depende de ninguna otra operación del módulo.

### Tests for User Story 1 ⚠️

> **NOTE: Escribir estas pruebas PRIMERO y comprobar que FALLAN antes de implementar**

- [ ] T011 [US1] Escribir `tests/CuentasBancarias.Api.Tests/CrearCuentaTests.cs` con los escenarios de aceptación 1–8 de US1 y los casos borde (recorte de `"  Ana Pérez  "`; titular de 100 caracteres válido y de 101 inválido; saldo `"1000"` como texto inválido; `1000000.00` válido y `1000000.01` inválido; `1000.001` inválido y `1000.100` válido; campos extra ignorados; `"Titular"` con mayúscula cuenta como titular faltante; cuerpo que no es objeto → `errors[""]`; JSON mal formado → `400`); verifica el `201` con header `Location: /cuentas/{id}` y, en cada rechazo, que no se creó ninguna fila en SQLite (FR-001, FR-002, FR-002a, FR-003, FR-003a, FR-004, FR-005, FR-009, FR-010, FR-011; R2, R6, R7; `POST /cuentas`)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Crear `src/CuentasBancarias.Api/Cuentas/CrearCuentaValidator.cs`: recorre el `JsonElement` crudo, evalúa `titular` y `saldo` por separado y junta **todos** los errores en `Dictionary<string, string[]>` según la tabla de data-model (Petición de creación): nombres exactos en minúsculas, `titular` string recortado no vacío de ≤ 100 caracteres, `saldo` con `ValueKind == Number`, `TryGetDecimal`, `0 ≤ saldo ≤ 1_000_000.00` y `decimal.Round(saldo, 2) == saldo`; cuerpo que no es objeto → clave `""` (FR-002, FR-002a, FR-003, FR-003a; R2)
- [ ] T013 [US1] Agregar `POST /cuentas` en `src/CuentasBancarias.Api/Cuentas/CuentasEndpoints.cs`: recibe el cuerpo como `JsonElement`, valida con `CrearCuentaValidator` y responde `Results.ValidationProblem(errores)` si hay errores; si no, crea la cuenta con `Guid.CreateVersion7()` y el titular recortado, la guarda con `CuentaStore.Insertar` y responde `201` con `Location: /cuentas/{id}` y el cuerpo `{ id, titular, saldo }` (FR-001, FR-004, FR-005; R2, R6, R7; `POST /cuentas`)

**Checkpoint**: `CrearCuentaTests` pasa completo; US1 funciona sin la operación de consulta.

---

## Phase 4: User Story 2 - Consultar cuenta bancaria (Priority: P1)

**Goal**: Un cliente autorizado consulta una cuenta por su identificador y recibe identificador, titular y saldo.

**Independent Test**: Se prueba sembrando una cuenta directamente en el almacenamiento (sin pasar por la operación de crear) y consultándola por su identificador. No depende de que la operación de crear esté implementada.

### Tests for User Story 2 ⚠️

> **NOTE: Escribir estas pruebas PRIMERO y comprobar que FALLAN antes de implementar**

- [ ] T014 [P] [US2] Escribir `tests/CuentasBancarias.Api.Tests/ConsultarCuentaTests.cs`: escenarios de aceptación 1–4 de US2 con la cuenta sembrada con `ApiFactory.SembrarCuenta`, sin usar `POST /cuentas`; un GUID inexistente y un identificador con formato inválido (`no-es-un-guid`) devuelven `404` indistinguibles: mismo `status`, mismo `title` (`"Not Found"`) y sin `detail` ni datos internos (el `traceId` que agrega `AddProblemDetails` varía por petición y no se compara); sin credencial responde `401` aunque la cuenta exista (FR-007, FR-008, FR-009, FR-010, FR-011, FR-012; R3, R6, R7, R8; `GET /cuentas/{id}`)
- [ ] T015 [P] [US2] Escribir `tests/CuentasBancarias.Api.Tests/PersistenciaTests.cs`: crea una cuenta con `POST /cuentas` en una `ApiFactory`, la libera, levanta otra sobre el **mismo** archivo SQLite y la consulta con `GET /cuentas/{id}` → `200` con los mismos datos (FR-006; R4, R8; `POST /cuentas`, `GET /cuentas/{id}`)

### Implementation for User Story 2

- [ ] T016 [US2] Agregar `GET /cuentas/{id}` en `src/CuentasBancarias.Api/Cuentas/CuentasEndpoints.cs`: `{id}` como `string`, sin restricción de ruta `:guid`; si `Guid.TryParse` falla o `CuentaStore.Obtener` devuelve `null`, responde el mismo `404` Problem Details (`title: "Not Found"`, sin `detail`); si existe, `200` con `{ id, titular, saldo }` (FR-007, FR-008; R6, R7; `GET /cuentas/{id}`)

**Checkpoint**: `ConsultarCuentaTests` y `PersistenciaTests` pasan; US1 y US2 funcionan cada una por su cuenta.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validar la feature de punta a punta con la API real y cerrar los criterios de éxito.

- [ ] T017 Escribir `specs/001-cuentas-bancarias/cobertura.md`: una tabla que lleva cada caso de "Cobertura mínima de pruebas" de `specs/001-cuentas-bancarias/plan.md` y cada criterio SC-001…SC-006 a la prueba que lo cubre (archivo y método) o, si no lo cubre una prueba (SC-005), a su paso de `quickstart.md`; al final, la salida completa de `dotnet test` sobre `CuentasBancarias.slnx`, toda en verde (FR-006, FR-009, FR-010, FR-011; SC-001, SC-002, SC-003, SC-004, SC-005, SC-006; `POST /cuentas`, `GET /cuentas/{id}`)

La ejecución de `quickstart.md` de punta a punta contra la API real (crear, consultar, 400 con ambos campos, 401 sin cuerpo con JSON mal formado, 404 indistinguible, durabilidad tras reiniciar, la API no arranca sin la clave) es la **prueba manual** de esta fase: la hace el humano en el gate, no el ejecutor.

**Checkpoint**: `cobertura.md` muestra cada caso exigido por la constitución con su prueba, `dotnet test` pasa completo y el quickstart se verificó a mano.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias.
- **Foundational (Phase 2)**: Depende de Setup. Bloquea las historias.
- **User Story 1 (Phase 3)**: Depende de Foundational.
- **User Story 2 (Phase 4)**: Depende de Foundational **y de User Story 1**, solo por `PersistenciaTests` (T015), que crea la cuenta con `POST /cuentas`. El Independent Test de US2 (T014) no usa la operación de crear.
- **Polish (Phase 5)**: Depende de User Story 1 y User Story 2.

### User Story Dependencies

- **User Story 1 (P1)**: Sin dependencias con otras historias.
- **User Story 2 (P1)**: Sus escenarios de aceptación son independientes de US1 (siembra directa, FR-012). La prueba de durabilidad (T015) necesita US1.

### Within Each Phase

- Las pruebas se escriben primero y se comprueba que fallan (Principio II, FR-011).
- `Cuenta` antes que `CuentaStore`; middleware y store antes que `Program.cs`.
- `CrearCuentaValidator` antes que `POST /cuentas`.
- `CuentasEndpoints.cs` lo tocan T010, T013 y T016, en ese orden: no se paralelizan entre fases.

### Parallel Opportunities

- T004 en paralelo con T001–T003 una vez creado el proyecto.
- T007 en paralelo con T005/T006.
- T012 en paralelo con T011.
- T014 y T015 en paralelo.

---

## Parallel Example: User Story 2

```bash
Task: "Escribir ConsultarCuentaTests en tests/CuentasBancarias.Api.Tests/ConsultarCuentaTests.cs"
Task: "Escribir PersistenciaTests en tests/CuentasBancarias.Api.Tests/PersistenciaTests.cs"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Setup → Foundational (crítico: credencial y almacenamiento).
2. User Story 1 → **validar**: `CrearCuentaTests` en verde y creación a mano con el quickstart.

### Incremental Delivery

1. Setup + Foundational → la API rechaza todo lo que no trae credencial.
2. US1 → crear cuentas (MVP).
3. US2 → consultar cuentas y durabilidad.
4. Polish → mapa de cobertura versionado y quickstart de punta a punta en el gate humano.

La ejecución corre bajo el harness: cada fase de este archivo es una fase del harness, con gate humano y un commit al aprobarse (constitución v1.1.0).

---

## Notes

- [P] = archivos distintos, sin dependencias pendientes.
- [Story] mapea la tarea a su historia para la trazabilidad.
- Las citas entre paréntesis (FR, R#, rutas del contrato) son los anclajes que recibe el ejecutor de cada fase.
- Los checkboxes se marcan en el commit de la fase aprobada, no durante la fase.
