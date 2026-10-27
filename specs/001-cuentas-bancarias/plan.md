# Implementation Plan: Cuentas Bancarias

**Branch**: `001-cuentas-bancarias` | **Date**: 2026-10-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-cuentas-bancarias/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

API HTTP con dos operaciones, crear cuenta (`POST /cuentas`) y consultar cuenta
(`GET /cuentas/{id}`), protegidas por una credencial de cliente única enviada en
el header `X-Api-Key`. Se implementa como ASP.NET Core Minimal API sobre .NET 10,
con persistencia durable en un archivo SQLite accedido con `Microsoft.Data.Sqlite`
(sin ORM). La validación de la petición de creación se hace sobre el JSON crudo
para poder reportar todos los campos inválidos a la vez y rechazar saldos
enviados como texto. Las pruebas de integración usan xUnit y
`WebApplicationFactory` contra una base SQLite temporal por prueba, y se escriben
antes de la implementación.

## Technical Context

**Language/Version**: C# 14 / .NET 10 (SDK 10.0.x)

**Primary Dependencies**: ASP.NET Core 10 (Minimal API, incluido en el SDK), `Microsoft.Data.Sqlite`

**Storage**: SQLite, un archivo local (`cuentas.db` por defecto, configurable). Tabla única `Cuentas`; saldo guardado en centavos (`INTEGER`).

**Testing**: xUnit + `Microsoft.AspNetCore.Mvc.Testing` (`WebApplicationFactory<Program>`), pruebas de integración in-process

**Target Platform**: Servicio HTTP multiplataforma (Kestrel); desarrollo en Windows 11

**Project Type**: web-service (API REST, sin frontend)

**Performance Goals**: Crear o consultar en < 1 s en condiciones normales (SC-005); sin objetivo de throughput

**Constraints**: Credencial validada antes de leer el cuerpo (FR-010); secreto solo en configuración o entorno; durabilidad tras reinicio (FR-006)

**Scale/Scope**: Uso de ejercicio: un cliente, volumen bajo, sin requisitos de concurrencia

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitución v1.0.0.

| Principio / regla | Cómo lo cumple este plan | Estado |
|---|---|---|
| **I. API-First con contrato explícito** | `contracts/openapi.yaml` define ruta, request, response y códigos de error de `POST /cuentas` y `GET /cuentas/{id}` antes de implementar. | ✅ PASS |
| **II. Test-First** | Pruebas de integración con `WebApplicationFactory` escritas y fallando antes de cada endpoint. Cobertura mínima por endpoint en la tabla de abajo. | ✅ PASS |
| **III. Simplicidad (YAGNI)** | Minimal API sin controladores, sin ORM, sin capa de servicios ni interfaces de repositorio. Dependencias nuevas justificadas abajo. Una sola clase `CuentaStore` concentra el SQL; se justifica abajo. | ✅ PASS |
| **IV. Seguridad básica** | Middleware de API key aplicado a toda petición, antes del enrutamiento al endpoint. Secreto en `Auth:ApiKey` (variable de entorno o user-secrets, nunca en `appsettings.json` versionado). Credencial ausente, vacía o incorrecta → `401` con cuerpo vacío, idéntico en los tres casos. Comparación en tiempo constante. | ✅ PASS |
| **Restricción: stack** | .NET 10, ASP.NET Core Web API, SQLite, xUnit, según el enunciado del ejercicio. | ✅ PASS |
| **Restricción: alcance** | Solo crear y consultar. Sin listado, borrado, depósitos, retiros, transferencias, login ni roles (FR-013). | ✅ PASS |
| **Flujo de trabajo** | El plan pasa el Constitution Check antes de escribir código. Un commit por tarea en `/speckit-implement`. | ✅ PASS |

**Cobertura mínima de pruebas (Principio II)**:

| Caso exigido | `POST /cuentas` | `GET /cuentas/{id}` |
|---|---|---|
| Caso exitoso | 201 con la cuenta creada | 200 con una cuenta sembrada directo en SQLite (FR-012) |
| Recurso inexistente | No aplica (crear no busca un recurso) | 404 con un GUID que no existe |
| Sin credencial | 401, y no se crea ninguna cuenta | 401, incluso si la cuenta existe |
| Datos incompletos / inválidos | 400 nombrando cada campo faltante o inválido | 404 con un identificador de formato inválido (escenario 3 de US2) |

**Justificación de dependencias y piezas (Principio III)**:

- `Microsoft.Data.Sqlite`: es el proveedor ADO.NET oficial de SQLite y la forma mínima de cumplir la durabilidad con el stack fijado. Se descartó EF Core porque una tabla y dos consultas no justifican DbContext ni migraciones.
- `Microsoft.AspNetCore.Mvc.Testing` (solo en pruebas): levanta la API en memoria para las pruebas de integración que exige el Principio II.
- `CuentaStore`: una clase concreta, sin interfaz, con `Insertar`, `Obtener` y la creación del esquema. Evita repetir SQL y la conversión centavos↔decimal en dos endpoints. No es una capa de servicios.
- No se agrega `Microsoft.AspNetCore.OpenApi` ni Swagger: el contrato vive en `contracts/openapi.yaml` y la API no necesita servirlo.

**Re-check post-diseño (Phase 1)**: ✅ PASS. El diseño de `data-model.md`, `contracts/openapi.yaml` y `quickstart.md` no agrega dependencias, capas ni operaciones fuera de las listadas arriba.

## Project Structure

### Documentation (this feature)

```text
specs/001-cuentas-bancarias/
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Phase 0 (/speckit-plan)
├── data-model.md        # Phase 1 (/speckit-plan)
├── quickstart.md        # Phase 1 (/speckit-plan)
├── contracts/
│   └── openapi.yaml     # Phase 1 (/speckit-plan)
├── checklists/
│   └── requirements.md  # /speckit-specify
└── tasks.md             # Phase 2 (/speckit-tasks, NO lo crea /speckit-plan)
```

### Source Code (repository root)

```text
CuentasBancarias.slnx

src/
└── CuentasBancarias.Api/
    ├── CuentasBancarias.Api.csproj
    ├── Program.cs                 # Configuración, middleware y mapeo de endpoints
    ├── appsettings.json           # Connection string; SIN la API key
    ├── Auth/
    │   └── ApiKeyMiddleware.cs    # Rechazo 401 antes de cualquier endpoint
    └── Cuentas/
        ├── Cuenta.cs              # record Cuenta(Guid Id, string Titular, decimal Saldo)
        ├── CuentasEndpoints.cs    # POST /cuentas, GET /cuentas/{id}
        ├── CrearCuentaValidator.cs# Valida el JSON crudo y junta todos los errores
        └── CuentaStore.cs         # SQL contra SQLite y creación del esquema

tests/
└── CuentasBancarias.Api.Tests/
    ├── CuentasBancarias.Api.Tests.csproj
    ├── ApiFactory.cs              # WebApplicationFactory con SQLite temporal y API key de prueba
    ├── CrearCuentaTests.cs        # US1
    ├── ConsultarCuentaTests.cs    # US2 (siembra directa en SQLite)
    └── PersistenciaTests.cs       # SC-001: la cuenta sobrevive a reiniciar la app
```

**Structure Decision**: Un proyecto de API y un proyecto de pruebas, organizados
por feature (`Cuentas/`) en lugar de por capa técnica, porque solo hay una entidad
y dos endpoints. No hay `tests/unit/` ni `tests/contract/`: la constitución exige
pruebas de integración, y el contrato se verifica a través de ellas.

## Complexity Tracking

No hay violaciones al Constitution Check que justificar.
