# SSD Cuenta Bancaria API Constitution

## Core Principles

### I. API-First con contrato explícito
Cada endpoint se define antes de implementarse. El contrato DEBE incluir:
- ruta
- request
- response
- códigos de error

Ningún endpoint se implementa sin contrato aprobado en el plan de la feature.

### II. Test-First
Toda funcionalidad nace con una prueba que falla primero.
Mínimo obligatorio: pruebas de integración sobre cada endpoint cubriendo
el caso exitoso, el recurso inexistente, la llamada sin credencial y los
datos incompletos.

### III. Simplicidad
Aplicar la regla YAGNI ("You Aren't Gonna Need It"). Sin capas no
solicitadas o no justificadas, sin login, sin roles. Una dependencia o
capa nueva se agrega si y solo si resuelve un problema real del alcance,
y la justificación se documenta por escrito en el plan de la feature.

### IV. Seguridad básica obligatoria
Ningún endpoint acepta llamadas anónimas: toda petición presenta una
credencial de cliente. El secreto vive en configuración o entorno, nunca
en código fuente. Un rechazo no revela el motivo del fallo.

## Restricciones técnicas

- El stack definido en el enunciado del ejercicio no se cambia sin enmienda.
- El alcance se limita a dos operaciones: crear cuenta y consultar cuenta.
  Cualquier operación adicional requiere enmienda a esta constitución.

## Flujo de trabajo

- El flujo es obligatorio: specify, clarify, plan y tasks con Spec Kit; la ejecución, fase por fase, bajo el harness.
- Ningún código se escribe sin que el plan haya pasado el Constitution Check.
- Cada fase del harness se cierra con un commit propio al ser aprobada.

## Governance

El autor enmienda la constitución directamente y sube la versión semántica:
- MAJOR: quitar o redefinir un principio.
- MINOR: agregar un principio o ampliar una regla sin contradecir las existentes.
- PATCH: corregir redacción sin cambiar el significado.

Todo plan DEBE verificar el cumplimiento de estos principios en su
Constitution Check y justificar cualquier desviación.

**Version**: 1.1.0 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-27
