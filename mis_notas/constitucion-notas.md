Qué es la constitución en Spec Kit

Es el documento de reglas no negociables del proyecto. Todo lo demás del flujo (specify, plan, tasks, implement) la lee y se valida contra ella. En concreto, la plantilla de plan.md tiene una sección "Constitution Check" que obliga a justificar cualquier desviación antes de diseñar. Si la constitución queda vacía o genérica, esa validación no sirve de nada.

Qué hace el skill /speckit-constitution

1. Lee la plantilla y detecta los placeholders ([PROJECT_NAME], [PRINCIPLE_1_NAME], etc.).
2. Toma los principios que tú le des en el argumento o en la conversación. Si no das nada, intenta inferirlos del repo, y aquí no hay nada que inferir.
3. Rellena el documento con principios declarativos y verificables (MUST/SHOULD, no "debería ser bonito").
4. Revisa que las plantillas de spec, plan y tasks sigan alineadas con esos principios.
5. Antepone un "Sync Impact Report" como comentario HTML y asigna versión semántica. La primera vez será 1.0.0 con fecha de ratificación de hoy.

Lo que conviene decidir antes de correrlo

- Nombre del proyecto y de qué trata ssd01. Supongo que es un ejercicio de una serie, pero no sé el dominio ni el stack.
- Cuántos principios quieres. La plantilla trae cinco, pero puede tener tres o siete. Para un ejercicio, tres o cuatro suelen bastar.
- Qué principios reales quieres imponer. Ejemplos típicos: tests primero, simplicidad (YAGNI), un solo lenguaje o framework, documentación en español, sin dependencias externas salvo las aprobadas.
- Las dos secciones libres: una suele ser restricciones técnicas (stack, versiones) y la otra flujo de trabajo (cómo se revisa, qué gate hay que pasar antes de implementar).
- Gobernanza: quién aprueba cambios a la constitución. En un proyecto personal, basta con "el autor la enmienda y sube la versión".


1. Versionado semántico de la constitución

La constitución lleva versión MAJOR.MINOR.PATCH como si fuera software. El skill sube el número según el tipo de cambio:

- MAJOR (1.0.0 → 2.0.0): quitas un principio o lo redefines de forma que trabajo anterior ya no cumple. Ejemplo: tenías "Test-First obligatorio" y lo cambias a "las pruebas son opcionales". Todo plan aprobado bajo la regla vieja queda en duda.
- MINOR (1.0.0 → 1.1.0): agregas un principio o amplías uno sin contradecir lo anterior. Lo que ya existía sigue siendo válido, solo hay una regla nueva hacia adelante.
- PATCH (1.0.0 → 1.0.1): corriges redacción o aclaras sin cambiar el significado.

La idea es la misma que en una API: MAJOR rompe compatibilidad con lo ya hecho, MINOR suma, PATCH corrige. Cada spec y plan registra contra qué versión se validó, así sabes si una feature vieja necesita revisión cuando la constitución cambia.
