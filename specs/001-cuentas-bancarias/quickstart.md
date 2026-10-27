# Quickstart: Cuentas Bancarias

**Feature**: 001-cuentas-bancarias | **Plan**: [plan.md](./plan.md) | **Contrato**: [contracts/openapi.yaml](./contracts/openapi.yaml)

Guía para comprobar de punta a punta que la feature funciona. Los detalles de campos y reglas están en [data-model.md](./data-model.md); los de rutas y respuestas, en el contrato.

## Prerrequisitos

- SDK de .NET 10 (`dotnet --list-sdks` debe mostrar una versión `10.0.x`).
- `curl`, o cualquier cliente HTTP.

## 1. Pruebas de integración (validación principal)

Desde la raíz del repo:

```bash
dotnet test
```

**Resultado esperado**: todas las pruebas pasan. Como mínimo deben existir y pasar:

| Archivo | Cubre |
|---|---|
| `CrearCuentaTests` | Escenarios 1–8 de US1 y los edge cases de titular y saldo (recorte, 100 caracteres, texto numérico, 1.000.000,00 vs 1.000.000,01, más de 2 decimales, campos extra) |
| `ConsultarCuentaTests` | Escenarios 1–4 de US2, con la cuenta sembrada directo en SQLite |
| `PersistenciaTests` | SC-001: la cuenta sigue ahí tras reiniciar la app |

Las pruebas no necesitan configurar nada: cada una usa su propio archivo SQLite temporal y una API key de prueba.

## 2. Ejecución manual

Configura la credencial fuera del código (una sola vez):

```bash
dotnet user-secrets set "Auth:ApiKey" "clave-local-de-prueba" --project src/CuentasBancarias.Api
```

Levanta la API:

```bash
dotnet run --project src/CuentasBancarias.Api
```

La consola muestra la URL (por ejemplo `http://localhost:5000`). En los ejemplos siguientes, `$URL` es esa dirección.

### Crear una cuenta → 201

```bash
curl -i -X POST "$URL/cuentas" \
  -H "X-Api-Key: clave-local-de-prueba" \
  -H "Content-Type: application/json" \
  -d '{"titular":"  Ana Pérez  ","saldo":1000}'
```

Esperado: `201 Created`, header `Location: /cuentas/{id}` y un cuerpo con `id`, `titular: "Ana Pérez"` (recortado) y `saldo: 1000`.

### Consultar la cuenta → 200

```bash
curl -i "$URL/cuentas/{id}" -H "X-Api-Key: clave-local-de-prueba"
```

Esperado: `200 OK` con la misma cuenta.

### Errores de validación → 400 con todos los campos

```bash
curl -i -X POST "$URL/cuentas" \
  -H "X-Api-Key: clave-local-de-prueba" \
  -H "Content-Type: application/json" \
  -d '{"titular":"   ","saldo":"1000"}'
```

Esperado: `400` con `errors.titular` **y** `errors.saldo` en la misma respuesta.

### Sin credencial → 401 sin cuerpo

```bash
curl -i -X POST "$URL/cuentas" -H "Content-Type: application/json" -d '{basura'
```

Esperado: `401` sin cuerpo. **No** un 400, aunque el JSON esté mal formado: la credencial se revisa primero.

### Identificador inexistente o inválido → 404 idéntico

```bash
curl -i "$URL/cuentas/00000000-0000-0000-0000-000000000000" -H "X-Api-Key: clave-local-de-prueba"
curl -i "$URL/cuentas/no-es-un-guid"                        -H "X-Api-Key: clave-local-de-prueba"
```

Esperado: ambas respuestas son `404` con el mismo cuerpo.

### Durabilidad

Detén la API (Ctrl+C), vuelve a levantarla y repite la consulta del paso "Consultar la cuenta". Esperado: `200` con la misma cuenta. El archivo `cuentas.db` queda en el directorio de trabajo de la API.

## 3. Sin credencial configurada

Si `Auth:ApiKey` no está configurada, la API **no arranca** y muestra un error de configuración. Es intencional (fail-closed, ver [research.md R3](./research.md#r3-credencial-de-cliente-y-orden-auth-antes-de-validar)).
