# Especifications

## La regla de oro 
Cada user story es un incremento independiente y probable por sí sola. Las historias P1 solas forman el MVP; P2 agrega valor encima. Si tu historia P2 no puede probarse sin "acabar el mundo", el corte está mal hecho.

⚠️ Error clásico de principiante: dividir por capas técnicas (P1: "crear modelo", P2: "crear endpoint"). Las historias se dividen por valor para el usuario, no por componentes.

## Ejemplo de una Especificacion

### User Story 1 - Crear plan de ahorro (Priority: P1)
    Como cliente, quiero crear un plan de ahorro con condiciones definidas, para poder empezar a guardar dinero con un objetivo claro.

### Why this priority:
 Es la funcionalidad base: sin planes creados no existe ningún dato en el sistema y ninguna otra operación es posible. Entrega valor mínimo de forma aislada: el cliente ya puede registrar planes.

### Independent Test: 
Puede probarse enviando una solicitud de creación con datos válidos e inválidos, verificando que el plan se persiste con su identificador. Entrega valor sin necesitar ninguna otra funcionalidad.

## Acceptance Scenarios:

**Given**  un cliente con datos válidos (nombre del titular, tipo de plan, monto objetivo), When envía la solicitud de creación, Then el plan se crea con estado "activo" y se devuelve el ID generado con código 201.

**Given** una solicitud sin el nombre del titular, When se envía, Then se rechaza con código 400 indicando el campo faltante.

**Given** un monto objetivo inferior al mínimo permitido ($25), When se envía la solicitud, Then se rechaza con código 400 explicando la regla de negocio violada.

**Given** un titular que ya alcanzó el máximo de planes activos (3), When intenta crear otro, Then se rechaza con código 409.


## Requirements (sección hermana de las stories)
Functional Requirements
FR-001: El sistema DEBE generar un identificador único por plan
FR-002: El sistema DEBE validar el monto mínimo al crear
...
Key Entities
Plan: ID, titular, tipo, monto objetivo, estado, fecha de creación


Prioridad ≠ Dependencia: dos ejes distintos
Esta es una de las confusiones más comunes al escalar a muchas historias. La respuesta corta:

No cambies la prioridad para expresar una dependencia. Mantén la prioridad como indicador de valor y documenta la dependencia explícitamente por separado. Solo reordenas si la dependencia cambia el orden de entrega del valor.

Primero, una aclaración sobre los niveles P
En spec-kit los niveles P son cubos gruesos, no un ranking 1-a-N:

Nivel
Significado
Con 8 historias podría ser
P1	MVP — imprescindible	US1, US2, US3
P2	Should — valor claro	US4, US5, US6
P3	Nice to have	US7, US8