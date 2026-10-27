# Tasks

## Qué es el paso tasks en Spec Kit

Es la última fase de diseño, y viene después de plan. El plan dice **cómo** se construye: stack, estructura del código y decisiones técnicas. Tasks lo parte en tareas concretas y ordenadas, cada una con la ruta del archivo que toca, agrupadas por historia de usuario para que cada historia se pueda construir y probar por separado.

En el flujo original de Spec Kit, después de tasks sigue `/speckit-implement`. En este repo **no**: desde la constitución v1.1.0, la ejecución la hace el harness, fase por fase (ver [puente-speckit-harness.md](../docs/puente-speckit-harness.md)).

## Qué hace el skill /speckit-tasks

1. Corre `setup-tasks.ps1`, que ubica la carpeta de la feature y la plantilla `tasks-template.md`.
2. Lee `plan.md` y `spec.md` (obligatorios) y, si existen, `data-model.md`, `contracts/`, `research.md`, `quickstart.md` y la constitución.
3. Arma las fases fijas:
   - **Setup**: estructura y dependencias.
   - **Foundational**: lo que bloquea a todas las historias.
   - **Una fase por historia**, en orden de prioridad, con su objetivo, su Independent Test, las pruebas (si se pidieron) y la implementación.
   - **Polish**: lo transversal.
4. Cada tarea sigue el formato estricto `- [ ] T001 [P] [US1] Descripción con ruta`:
   - `[P]` marca las tareas que pueden ir en paralelo (archivos distintos, sin dependencias pendientes).
   - `[US1]` dice a qué historia pertenece la tarea.
5. Agrega la sección "Dependencies & Execution Order", los ejemplos de paralelismo y la estrategia (MVP primero).

Ojo: **las pruebas son opcionales** para el skill. Solo genera tareas de prueba si la spec o el usuario las piden. Aquí las pide FR-011 y el Principio II de la constitución (test-first).

## El argumento de trazabilidad

Corrí el skill con este argumento:

> cada tarea cita entre paréntesis los FR, las decisiones de research (R#) y las rutas del contrato que implementa

Es un **argumento, no un cambio a spec-kit**. Existe por el puente con el harness:

- Al abrir el ticket, cada fase del harness recibe en `anclajes` las secciones exactas que necesita (`spec.md#FR-003`, `research.md#R2`, la ruta del contrato).
- El ejecutor lee solo esos anclajes, no la spec completa. El escéptico recibe los mismos.
- Esos anclajes salen de las citas de cada tarea. Sin citas, la traducción tendría que adivinarlos.

## Lo que salió en el ejercicio (feature 001-cuentas-bancarias)

**17 tareas en 5 fases** (eran 18; la revisión cambió Polish, ver abajo):

| Fase | Tareas | Qué entrega |
|---|---|---|
| Setup | T001–T004 | Solución `.slnx`, proyecto API, proyecto de pruebas, los dos paquetes justificados en `plan.md` |
| Foundational | T005–T010 | `ApiFactory`, pruebas de autenticación, `Cuenta`, `CuentaStore`, `ApiKeyMiddleware`, `Program.cs` |
| US1 Crear | T011–T013 | `CrearCuentaTests`, `CrearCuentaValidator`, `POST /cuentas` |
| US2 Consultar | T014–T016 | `ConsultarCuentaTests`, `PersistenciaTests`, `GET /cuentas/{id}` |
| Polish | T017 | `cobertura.md`: cada caso exigido por la constitución con su prueba, más `dotnet test` en verde. El quickstart lo corre el humano en el gate |

- **Los 15 FR quedaron citados en alguna tarea**, incluido FR-013. Ese es el negativo ("MUST NOT exponer…"), y quedó en `Program.cs`, que no mapea ninguna otra ruta.
- La única tarea sin FR ni R# es T007 (`Cuenta.cs`), que cita la sección de `data-model.md`.
- Tres fases tienen pruebas escritas primero: Foundational, US1 y US2.

### Decisiones que vale la pena recordar

- **Foundational tiene sus propias pruebas** (`AutenticacionTests`): 401 idéntico con la credencial ausente, vacía o incorrecta; 401 y no 400 ante JSON mal formado; y la API no arranca sin `Auth:ApiKey`. Así esa fase tiene algo comprobable en el gate humano, y no queda como "infraestructura que se verifica después".
- **`PersistenciaTests` va en US2, no en Polish.** Necesita crear (US1) y consultar (US2). Si fuera en Polish, la prueba pasaría desde el primer momento y no habría corrida en rojo que mostrar. En US2 falla antes de implementar el `GET`, como pide test-first. Costo: US2 depende de US1, solo por esa prueba. Los escenarios de US2 siguen sembrando directo en SQLite (FR-012).
- **`CuentasEndpoints.cs` nace vacío en Foundational.** `Program.cs` ya llama a `MapCuentasEndpoints()`, y cada historia agrega su ruta. Ninguna historia tiene que tocar `Program.cs`.
- **T002 borra el `UnitTest1.cs` de la plantilla xUnit**, para que no quede una prueba vacía en la solución.

### Lo que cambió con la revisión de la rama

Un revisor independiente probó el plan contra lo que de verdad hace .NET, y cuatro tareas tenían problemas:

- **T001 y la plantilla.** `dotnet new web` trae `app.MapGet("/", …)`, que la regla `solo_dos_endpoints` marca como error: `fase_1` iba a fallar en su primer intento. Ahora T001 pide quitarlo.
- **T001 y los user-secrets.** `dotnet user-secrets set` falla si el proyecto no tiene `UserSecretsId`. Ahora T001 corre `dotnet user-secrets init`, y `quickstart.md` lo explica.
- **T014 y el "mismo cuerpo".** `AddProblemDetails` agrega un `traceId` distinto en cada respuesta, así que dos 404 nunca son idénticos byte a byte. Ahora se comparan `status`, `title` y la ausencia de `detail`.
- **Polish sin código.** El harness juzga el diff. Una fase que solo ejecuta y comprueba no deja nada que compilar ni que leer. Ahora Polish entrega `cobertura.md`, que sí está versionado, y el quickstart pasa a ser la prueba manual del humano.

## Lo que aprendí

- **La trazabilidad se pide, no viene sola.** La plantilla de tasks no cita requisitos. Sin el argumento, las tareas dirían "implementar endpoint" sin decir qué FR cumplen.
- **Una tarea por línea.** El formato estricto deja verificar las tareas con una regex: `verificar_traduccion.py` las cuenta y comprueba que ninguna se pierda al pasar a `plan.json`. Mi primera versión de T011 tenía sub-viñetas, y la cita quedaba lejos de la tarea.
- **Dónde va una prueba depende de cuándo puede fallar.** Test-first no es solo escribir la prueba antes: tiene que poder estar en rojo en ese momento. Eso decidió la ubicación de `PersistenciaTests`.
- **Una tarea tiene que sobrevivir a la herramienta real.** "Crear el proyecto" parecía obvio, pero la plantilla trae un endpoint y no trae `UserSecretsId`. Esas dos cosas solo se ven corriendo `dotnet new`, no leyendo la spec.
- **En un harness basado en el diff, cada fase tiene que entregar algo versionado.** Si no, el escéptico no tiene qué juzgar.
- **Ubicar los FR negativos.** "MUST NOT" no se implementa; se respeta. Igual tiene que quedar anclado en alguna fase, porque si no, el verificador lo marca como FR perdido. Además lo vigila una regla (`solo_dos_endpoints`).

## Después de tasks

1. Commit de `tasks.md` y esta nota (`spec(001): add traceable tasks`).
2. `/ticket-abrir-sdd specs/001-cuentas-bancarias` para abrir el ticket del harness.
3. Ejecutar fase por fase con `/fase fase_1`.
