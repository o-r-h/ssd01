# Feature Specification: Cuentas Bancarias

**Feature Branch**: `001-cuentas-bancarias`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "Módulo de cuentas bancarias con dos operaciones: crear cuenta y consultar cuenta. Toda operación exige credencial de cliente. Pruebas de integración antes de la implementación. Fuera de alcance: login, usuarios, roles, depósitos, retiros, transferencias, listado y borrado de cuentas."

## Clarifications

### Session 2026-10-13

- Q: ¿Las cuentas deben sobrevivir a un reinicio del servicio? → A: Sí, durable: una cuenta creada sigue existiendo tras reiniciar el servicio.
- Q: Si varios campos son inválidos a la vez, ¿el error los nombra todos o solo el primero? → A: Todos: el error lista cada campo inválido o faltante de la petición.
- Q: ¿El titular se guarda tal cual o se recortan los espacios al inicio y al final? → A: Se recorta antes de validar y guardar; el límite de 100 caracteres se mide sobre el valor recortado.
- Q: ¿Hay un saldo inicial máximo? → A: Sí, 1.000.000,00 inclusive; valores mayores se rechazan como inválidos nombrando el campo saldo.
- Q: ¿Se acepta un saldo enviado como texto numérico (p. ej. "1000")? → A: No: el saldo debe enviarse como número; cualquier texto, numérico o no, se rechaza como inválido.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear cuenta bancaria (Priority: P1)

Un cliente autorizado del módulo envía el nombre del titular y un saldo inicial.
El sistema valida los datos, genera un identificador único para la cuenta,
la guarda y devuelve la cuenta creada con su identificador.

**Why this priority**: Sin cuentas creadas el módulo no tiene datos sobre los
que operar. Es la operación de entrada de todo el sistema.

**Independent Test**: Se prueba enviando una petición de creación con datos
válidos y verificando que la respuesta contiene un identificador único y los
datos enviados. No depende de ninguna otra operación del módulo.

**Acceptance Scenarios**:

1. **Given** un cliente con credencial válida, **When** envía titular "Ana Pérez" y saldo inicial 1000, **Then** recibe la cuenta creada con un identificador único, titular "Ana Pérez" y saldo 1000.
2. **Given** un cliente con credencial válida, **When** envía titular "Ana Pérez" y saldo inicial 0, **Then** recibe la cuenta creada con saldo 0.
3. **Given** un cliente con credencial válida, **When** envía titular vacío, **Then** recibe un error de validación que identifica el campo titular como inválido y no se crea ninguna cuenta.
4. **Given** un cliente con credencial válida, **When** envía saldo inicial negativo, **Then** recibe un error de validación que identifica el campo saldo como inválido y no se crea ninguna cuenta.
5. **Given** un cliente con credencial válida, **When** envía una petición sin el campo titular o sin el campo saldo, **Then** recibe un error de validación que identifica el campo faltante.
6. **Given** un cliente sin credencial o con credencial incorrecta, **When** intenta crear una cuenta, **Then** la petición es rechazada sin indicar el motivo y no se crea ninguna cuenta.
7. **Given** dos peticiones de creación con los mismos datos, **When** ambas se procesan, **Then** se crean dos cuentas distintas con identificadores diferentes.
8. **Given** un cliente con credencial válida, **When** envía titular vacío y saldo inicial negativo en la misma petición, **Then** recibe un único error de validación que nombra ambos campos, titular y saldo, y no se crea ninguna cuenta.

---

### User Story 2 - Consultar cuenta bancaria (Priority: P1)

Un cliente autorizado pide una cuenta por su identificador y recibe el
identificador, el titular y el saldo actual.

**Why this priority**: Un módulo que crea cuentas pero no permite leerlas no
entrega valor verificable. Crear y consultar forman juntas el MVP mínimo.

**Independent Test**: Se prueba sembrando una cuenta directamente en el
almacenamiento (sin pasar por la operación de crear) y consultándola por su
identificador. No depende de que la operación de crear esté implementada.

**Acceptance Scenarios**:

1. **Given** una cuenta existente con identificador X, titular "Ana Pérez" y saldo 1000, **When** un cliente con credencial válida consulta X, **Then** recibe identificador X, titular "Ana Pérez" y saldo 1000.
2. **Given** ningún registro con identificador Y, **When** un cliente con credencial válida consulta Y, **Then** recibe un error de "no encontrado".
3. **Given** un identificador con formato inválido, **When** un cliente con credencial válida lo consulta, **Then** recibe un error de "no encontrado", sin exponer detalles internos.
4. **Given** un cliente sin credencial o con credencial incorrecta, **When** consulta cualquier identificador, **Then** la petición es rechazada sin indicar el motivo, incluso si la cuenta existe.

---

### Edge Cases

- Titular compuesto solo por espacios en blanco se trata como vacío.
- Titular con espacios al inicio o al final (p. ej. "  Ana Pérez  ") se recorta: la cuenta se guarda y se devuelve con titular "Ana Pérez".
- Saldo inicial con más de dos decimales se rechaza como inválido (ver Assumptions).
- Saldo inicial enviado como texto se rechaza como inválido, sea numérico ("1000") o no ("mil"); solo se acepta un valor numérico.
- Saldo inicial de exactamente 1.000.000,00 se acepta; 1.000.000,01 o más se rechaza como inválido.
- Titular con longitud excesiva se rechaza (límite en Assumptions).
- Petición de creación con campos adicionales no reconocidos: se ignoran.
- Credencial presente pero con valor vacío se trata como credencial incorrecta.
- El rechazo por credencial ocurre antes de cualquier validación de datos, de modo que un cliente no autorizado no obtiene pistas sobre el formato esperado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir crear una cuenta a partir de un titular y un saldo inicial.
- **FR-002**: El sistema MUST rechazar la creación cuando el titular esté ausente, vacío o compuesto solo de espacios, indicando el campo en el error.
- **FR-002a**: El sistema MUST recortar los espacios al inicio y al final del titular antes de validarlo y guardarlo; el valor recortado es el que se persiste y se devuelve.
- **FR-003**: El sistema MUST rechazar la creación cuando el saldo inicial esté ausente, no se envíe como valor numérico (un texto, aunque contenga dígitos, es inválido), sea negativo o supere 1.000.000,00, indicando el campo en el error. El valor 1.000.000,00 exacto es válido.
- **FR-003a**: Cuando una petición de creación tenga varios campos inválidos o faltantes, el error de validación MUST listarlos todos, no solo el primero encontrado.
- **FR-004**: El sistema MUST generar un identificador único para cada cuenta creada; dos cuentas nunca comparten identificador.
- **FR-005**: El sistema MUST devolver la cuenta creada (identificador, titular, saldo) como respuesta a la creación exitosa.
- **FR-006**: El sistema MUST persistir las cuentas de forma durable: una cuenta creada puede consultarse después, incluso tras un reinicio del servicio.
- **FR-007**: El sistema MUST permitir consultar una cuenta por su identificador y devolver identificador, titular y saldo.
- **FR-008**: El sistema MUST responder con error de "no encontrado" cuando el identificador consultado no corresponde a ninguna cuenta.
- **FR-009**: Toda operación MUST exigir una credencial de cliente válida.
- **FR-010**: Ante credencial ausente o incorrecta, el sistema MUST rechazar la petición sin indicar el motivo del rechazo y antes de procesar los datos.
- **FR-011**: Cada operación MUST contar con pruebas de integración escritas antes de su implementación, que cubran: caso exitoso, recurso inexistente (consulta), petición sin credencial y datos incompletos o inválidos (creación).
- **FR-012**: Las pruebas de la operación de consulta MUST sembrar la cuenta directamente en el almacenamiento, sin usar la operación de crear.
- **FR-013**: El sistema MUST NOT exponer login, gestión de usuarios, roles, depósitos, retiros, transferencias, listado ni borrado de cuentas. Cualquiera de estas operaciones requiere enmienda a la constitución.

### Key Entities

- **Cuenta**: representa una cuenta bancaria. Atributos: identificador único generado por el sistema, titular (texto no vacío, sin espacios al inicio ni al final, de hasta 100 caracteres), saldo (valor monetario entre 0 y 1.000.000,00 inclusive, con hasta dos decimales). No tiene relaciones con otras entidades en esta feature.
- **Cliente autorizado**: cualquier consumidor del módulo que presenta una credencial válida. No se modela como entidad persistida; no hay usuarios ni roles.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un cliente autorizado crea una cuenta con datos válidos y la recupera por su identificador en el 100% de los intentos, incluso después de reiniciar el servicio.
- **SC-002**: El 100% de las peticiones con titular vacío o saldo negativo son rechazadas con un error que nombra todos los campos inválidos.
- **SC-003**: El 100% de las peticiones sin credencial o con credencial incorrecta son rechazadas, sin diferencia observable entre ambos casos.
- **SC-004**: Consultar un identificador inexistente devuelve "no encontrado" en el 100% de los casos, sin exponer información interna.
- **SC-005**: Crear o consultar una cuenta responde en menos de 1 segundo en condiciones normales.
- **SC-006**: Cada operación tiene pruebas de integración para los cuatro casos exigidos, y todas pasan antes de dar la feature por terminada.

## Assumptions

- El titular se limita a 100 caracteres medidos tras recortar espacios al inicio y al final; longitudes mayores se rechazan como inválidas.
- El saldo se expresa en una única moneda implícita; no se modela el campo moneda en esta feature.
- El saldo acepta hasta dos decimales; valores con más precisión se rechazan.
- Existe una única credencial de cliente compartida, configurada fuera del código. No hay credenciales por cliente ni rotación en esta feature.
- Los identificadores son opacos para el cliente; su formato lo decide el plan.
- No hay requisitos de concurrencia ni de volumen más allá de un uso de ejercicio.
- Las cuentas no se modifican ni eliminan una vez creadas dentro del alcance de esta feature.
