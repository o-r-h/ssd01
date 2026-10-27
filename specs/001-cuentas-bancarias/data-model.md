# Data Model: Cuentas Bancarias

**Feature**: 001-cuentas-bancarias | **Date**: 2026-10-26 | **Plan**: [plan.md](./plan.md)

## Entidad: Cuenta

Representa una cuenta bancaria. Se crea una vez y no se modifica ni se elimina en esta feature, así que no tiene transiciones de estado.

| Campo | Tipo C# | Columna SQLite | JSON | Reglas |
|---|---|---|---|---|
| `Id` | `Guid` | `Id TEXT PRIMARY KEY` | `id` (string) | Lo genera el sistema (`Guid.CreateVersion7()`). Único (FR-004). Opaco para el cliente. |
| `Titular` | `string` | `Titular TEXT NOT NULL` | `titular` (string) | Se recorta antes de validar (FR-002a). No vacío tras recortar (FR-002). Máximo 100 caracteres sobre el valor recortado. |
| `Saldo` | `decimal` | `SaldoCentavos INTEGER NOT NULL` | `saldo` (number) | Entre 0 y 1.000.000,00 inclusive. A lo sumo 2 decimales. Debe llegar como número JSON, nunca como texto (FR-003). |

**Relaciones**: ninguna.

### Esquema SQLite

Se crea al arrancar la aplicación si no existe:

```sql
CREATE TABLE IF NOT EXISTS Cuentas (
    Id            TEXT    NOT NULL PRIMARY KEY,
    Titular       TEXT    NOT NULL,
    SaldoCentavos INTEGER NOT NULL
);
```

Conversión: `SaldoCentavos = Saldo * 100` al guardar y `Saldo = SaldoCentavos / 100m` al leer. Es exacta porque el validador garantiza que el saldo tiene como máximo 2 decimales. Ver [research.md R5](./research.md#r5-representación-del-saldo).

## Petición de creación (no persistida)

Es el cuerpo de `POST /cuentas`. Se valida sobre el JSON crudo, como se explica en [research.md R2](./research.md#r2-validación-que-lista-todos-los-errores-y-rechaza-saldo-como-texto). Se evalúan **todas** las reglas, y cada campo que falla aparece en la respuesta (FR-003a).

| Campo | Condición de error | Clave en `errors` |
|---|---|---|
| `titular` | Ausente | `titular` |
| `titular` | No es string (`null`, número, objeto...) | `titular` |
| `titular` | Vacío o solo espacios tras recortar | `titular` |
| `titular` | Más de 100 caracteres tras recortar | `titular` |
| `saldo` | Ausente | `saldo` |
| `saldo` | No es número JSON (incluye `"1000"` y `null`) | `saldo` |
| `saldo` | Negativo | `saldo` |
| `saldo` | Mayor que 1.000.000,00 | `saldo` |
| `saldo` | Más de 2 decimales significativos | `saldo` |
| *(cuerpo)* | No es un objeto JSON | `""` |

Los campos que no se reconocen se ignoran. Los nombres son sensibles a mayúsculas: `Titular` no equivale a `titular`.

## Cliente autorizado (no persistido)

No es una entidad almacenada. Es cualquier petición cuyo header `X-Api-Key` coincide con el secreto `Auth:ApiKey` de la configuración. No hay usuarios ni roles.
