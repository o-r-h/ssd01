# Research: Cuentas Bancarias

**Feature**: 001-cuentas-bancarias | **Date**: 2026-10-26 | **Plan**: [plan.md](./plan.md)

El stack viene fijado por el enunciado: .NET 10, ASP.NET Core Web API, SQLite y xUnit. No quedaron
`NEEDS CLARIFICATION` en el Technical Context. Esta investigación resuelve cómo usar ese stack para cumplir
los requisitos de la spec que no son triviales.

## R1. Estilo de API: Minimal API o controladores

- **Decision**: Minimal API (`app.MapPost` / `app.MapGet`) en un archivo `CuentasEndpoints.cs`.
- **Rationale**: Son dos endpoints. Minimal API es el estilo por defecto de la plantilla `webapi` en .NET 10 y no necesita clases controlador, atributos ni el pipeline de MVC. Cumple el Principio III.
- **Alternatives considered**: Controladores (`dotnet new webapi --use-controllers`). Se descartaron porque agregan estructura (clases, filtros de MVC, model state) que no resuelve ningún problema del alcance.

## R2. Validación que lista todos los errores y rechaza saldo como texto

- **Decision**: El endpoint de creación recibe el cuerpo como `JsonElement` y `CrearCuentaValidator` lo recorre a mano. Revisa cada campo, junta todos los errores en un `Dictionary<string, string[]>` y responde `Results.ValidationProblem(errores)` si hay alguno.
- **Rationale**:
  - **FR-003a (todos los errores)**: si el cuerpo se deserializa a un DTO tipado y `saldo` llega como `"mil"`, System.Text.Json lanza una excepción en el primer campo con tipo incorrecto. Se pierde el error de `titular` y no se pueden reportar ambos. Sobre `JsonElement` cada campo se evalúa por separado.
  - **FR-003 (texto numérico rechazado)**: ASP.NET Core usa `JsonSerializerDefaults.Web`, que trae `NumberHandling = AllowReadingFromString`. Con un DTO tipado, `"1000"` se aceptaría como 1000 sin avisar, contra lo decidido en clarify. Con `JsonElement` se exige `ValueKind == JsonValueKind.Number`.
  - **Campos extra ignorados** (edge case): el validador solo lee `titular` y `saldo`.
- **Alternatives considered**:
  - DTO tipado + `NumberHandling = Strict` global: resuelve el texto numérico, pero no el reporte de todos los errores cuando hay un error de tipo.
  - Validación integrada de .NET 10 (`AddValidation` con DataAnnotations): corre después de deserializar, así que tiene el mismo problema con los errores de tipo.
  - FluentValidation: es una dependencia más para dos campos. Se descartó por el Principio III.

**Reglas de detalle**:

- Los nombres de propiedad se comparan **exactos y en minúsculas** (`titular`, `saldo`). `"Titular"` cuenta como campo no reconocido: se ignora y `titular` queda como faltante. Queda documentado en el contrato.
- `titular` debe ser un string JSON. Se recorta con `string.Trim()` (FR-002a) y luego se valida que no quede vacío y que tenga ≤ 100 caracteres, medidos con `string.Length` sobre el valor recortado.
- `saldo` debe ser un número JSON que `TryGetDecimal` acepte. Además debe cumplir `0 ≤ saldo ≤ 1_000_000.00` y `decimal.Round(saldo, 2) == saldo`. Por la última regla, `1000.100` se acepta (vale lo mismo que 1000.10) y `1000.001` se rechaza.
- `null` cuenta como valor inválido del campo. El mensaje es distinto de "falta el campo", pero el campo se nombra igual.
- Un cuerpo que no es un objeto JSON (array, `null`, número) produce un único error con clave `""`.

## R3. Credencial de cliente y orden "auth antes de validar"

- **Decision**: Middleware propio `ApiKeyMiddleware`, registrado con `app.UseMiddleware` antes de mapear los endpoints, de modo que corre antes de que se ejecute cualquier endpoint y, por lo tanto, antes de leer el cuerpo. Lee el header `X-Api-Key`, lo compara con `Auth:ApiKey` usando `CryptographicOperations.FixedTimeEquals` sobre los bytes UTF-8 y, si no coincide, responde `401` con cuerpo vacío sin llamar al siguiente paso del pipeline.
- **Rationale**:
  - **FR-010**: en Minimal API los *endpoint filters* se ejecutan **después** del binding del cuerpo. Si el JSON está mal formado, el usuario anónimo recibiría un 400 antes que el 401 y obtendría pistas del formato esperado. Un middleware corre antes de leer el cuerpo.
  - **SC-003**: header ausente, vacío o incorrecto pasan por la misma rama y producen la misma respuesta (401, sin cuerpo, sin `WWW-Authenticate` descriptivo).
  - Se aplica a toda ruta, incluso a las inexistentes. Así un anónimo tampoco puede distinguir qué rutas existen.
- **Alternatives considered**:
  - `AddAuthentication` con un `AuthenticationHandler` propio + `RequireAuthorization`: es el camino idiomático, pero son dos subsistemas (authN y authZ) para una sola clave compartida. Se descartó por el Principio III.
  - Endpoint filter: corre después del binding y viola FR-010.

**Secreto**: se lee de `Auth:ApiKey`. En desarrollo se configura con `dotnet user-secrets` o con la variable de entorno `Auth__ApiKey`. Nunca va en `appsettings.json` (Principio IV). Si la clave falta o está vacía al arrancar, la app falla al iniciar (fail-closed) en lugar de aceptar cualquier petición.

## R4. Persistencia SQLite sin ORM

- **Decision**: `Microsoft.Data.Sqlite` con SQL a mano en `CuentaStore`. El esquema se crea al arrancar con `CREATE TABLE IF NOT EXISTS`. Connection string en `ConnectionStrings:Cuentas` (por defecto `Data Source=cuentas.db`).
- **Rationale**: Una tabla, un `INSERT` y un `SELECT` por clave. Archivo en disco = durable entre reinicios (FR-006). Sin migraciones: si el esquema cambia en una feature futura, se decidirá entonces (YAGNI).
- **Alternatives considered**:
  - EF Core + `Microsoft.EntityFrameworkCore.Sqlite`: trae DbContext, migraciones y un proveedor que guarda `decimal` como TEXT. Es excesivo para el alcance.
  - Dapper: es una dependencia extra solo para ahorrar el mapeo de 3 columnas.
  - SQLite en memoria: viola FR-006.

## R5. Representación del saldo

- **Decision**: En C# el saldo es `decimal`. En SQLite se guarda como `INTEGER` en centavos (`saldo * 100`). En JSON va como número.
- **Rationale**: SQLite no tiene tipo decimal. `REAL` (double) introduce errores de redondeo en montos y `TEXT` obliga a parsear con cultura invariante. Los centavos enteros son exactos, y el máximo (100.000.000 centavos) cabe de sobra en un entero de 64 bits.
- **Alternatives considered**: `REAL` (impreciso), `TEXT` (exacto pero frágil por la cultura y no comparable numéricamente).

## R6. Identificador de cuenta

- **Decision**: `Guid` generado por la app con `Guid.CreateVersion7()`. Se guarda en SQLite como `TEXT` (formato `D`, minúsculas) con `PRIMARY KEY` y se expone como string en JSON.
- **Rationale**: Es único sin coordinar con la base (FR-004), opaco para el cliente (supuesto de la spec) y no permite adivinar cuántas cuentas hay, cosa que sí permitiría un entero autoincremental. La versión 7 es ordenable por tiempo y viene incluida desde .NET 9.
- **Alternatives considered**: `INTEGER AUTOINCREMENT` (expone el volumen y es secuencial), `Guid.NewGuid()` v4 (válido; v7 se prefiere solo por el orden de inserción).

**Formato inválido**: la ruta recibe `{id}` como `string`, sin restricción de ruta `:guid`. Si `Guid.TryParse` falla, el endpoint responde el mismo 404 que para un GUID inexistente (escenario 3 de US2, SC-004). Con la restricción de ruta, el 404 lo daría el enrutador con otro cuerpo, y se distinguirían ambos casos.

## R7. Formato de errores

- **Decision**: Problem Details (RFC 9457) vía `AddProblemDetails()`:
  - `400`: `ValidationProblemDetails` con `errors: { "titular": [...], "saldo": [...] }`.
  - `404`: `ProblemDetails` con `title: "Not Found"`, sin `detail` ni datos internos.
  - `401`: sin cuerpo.
- **Rationale**: Es el formato estándar que ASP.NET Core ya produce. `errors` permite nombrar varios campos en una sola respuesta (FR-003a, SC-002). Con `AddProblemDetails`, un JSON mal formado también devuelve un 400 con Problem Details, en vez de un 400 vacío o una página de excepción.
- **Alternatives considered**: formato de error propio. Se descartó porque obliga a documentarlo y mantenerlo sin ganar nada.

## R8. Estrategia de pruebas de integración

- **Decision**: `ApiFactory : WebApplicationFactory<Program>`. Cada instancia usa un archivo SQLite temporal único y una API key de prueba inyectada por configuración. Las pruebas de consulta siembran filas con un `SqliteConnection` propio y un `INSERT` directo (FR-012). La prueba de durabilidad crea la cuenta con una factory, la libera, levanta otra sobre el **mismo archivo** y consulta (SC-001).
- **Rationale**: Prueba la API real (pipeline, middleware, SQLite) sin red ni procesos externos. Un archivo por prueba evita dependencias entre pruebas.
- **Gotchas registrados**:
  - `Program` debe ser visible para el proyecto de pruebas. Se agrega `public partial class Program;` al final de `Program.cs`.
  - En Windows, el pool de conexiones de `Microsoft.Data.Sqlite` mantiene el archivo abierto. Antes de borrar el archivo temporal hay que llamar a `SqliteConnection.ClearAllPools()`.
- **Alternatives considered**: SQLite `:memory:` compartido (no prueba la durabilidad), `HttpClient` contra un proceso real (más lento y frágil).
