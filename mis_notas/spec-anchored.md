
Qué significa "Spec-Anchored"

En SDD (Spec-Driven Development) hay tres niveles según qué tan vivo es el spec:

┌────────────────┬─────────────────────────────────────────────────────────────────────┬──────────────────────────┐
│     Nivel      │                        Qué pasa con el spec                         │    Quién es la verdad    │
├────────────────┼─────────────────────────────────────────────────────────────────────┼──────────────────────────┤
│ Spec-First     │ Se escribe antes de codificar y luego se abandona                   │ El código                │
├────────────────┼─────────────────────────────────────────────────────────────────────┼──────────────────────────┤
│ Spec-Anchored  │ Se escribe antes y se mantiene junto al código. Cada cambio empieza │ Spec y código, en        │
│                │  por el spec                                                        │ sincronía                │
├────────────────┼─────────────────────────────────────────────────────────────────────┼──────────────────────────┤
│ Spec-as-Source │ El código se genera del spec. Los humanos no editan código          │ El spec                  │
└────────────────┴─────────────────────────────────────────────────────────────────────┴──────────────────────────┘

Elegiste Spec-Anchored. Eso impone tres reglas para todo el tutorial:

1. Ningún cambio de comportamiento empieza en el código. Primero se actualiza spec.md, después plan y tareas, después código.
2. El spec vive en el repo, en specs/001-crear-cuenta/, versionado con git igual que el código.
3. Al terminar, se verifica la sincronía. Para eso existe /speckit-converge: compara el código real contra spec y plan, y agrega lo que falta como tareas.

Mapa del tutorial

Cada paso produce un artefacto. Entre pasos nos detenemos a leerlo y analizarlo.

┌──────┬─────────────────────────┬──────────────────────────────────┬─────────────────────────────────────────────┐
│ Paso │         Comando         │            Artefacto             │            Pregunta que responde            │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 1    │ /speckit-constitution   │ .specify/memory/constitution.md  │ ¿Qué principios no negociables tiene el     │
│      │                         │                                  │ proyecto? (testing, simplicidad, seguridad) │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 2    │ /speckit-specify        │ specs/001-.../spec.md            │ ¿Qué debe hacer "crear cuenta bancaria" y   │
│      │                         │                                  │ por qué? Sin tecnología                     │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 3    │ /speckit-clarify        │ spec.md actualizado              │ ¿Qué ambigüedades quedan? Hasta 5 preguntas │
│      │ (opcional)              │                                  │  dirigidas                                  │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 4    │ /speckit-plan           │ plan.md, data-model.md,          │ ¿Cómo lo construimos? Aquí sí entra el      │
│      │                         │ contracts/                       │ stack                                       │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 5    │ /speckit-tasks          │ tasks.md                         │ ¿En qué orden y qué depende de qué?         │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 6    │ /speckit-analyze        │ reporte                          │ ¿Spec, plan y tareas se contradicen en      │
│      │ (opcional)              │                                  │ algo?                                       │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 7    │ /speckit-implement      │ código y pruebas                 │ Ejecución guiada por tasks.md               │
├──────┼─────────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────┤
│ 8    │ /speckit-converge       │ tasks.md ampliado                │ ¿Qué quedó sin construir respecto al spec?  │
│      │                         │                                  │ Aquí se ve el "anchored"                    │
└──────┴─────────────────────────┴──────────────────────────────────┴─────────────────────────────────────────────┘

Lo que necesito de ti antes del paso 1

- Git. La carpeta no es repositorio. Spec-kit crea una rama por feature (001-crear-cuenta). Con tu visto bueno hago git init antes de empezar.
- Alcance de "crear cuenta". Para el spec del paso 2 me sirve que pienses, sin tecnología todavía: ¿qué datos pide? ¿qué validaciones aplican (edad mínima, identificación única, moneda)? ¿qué pasa si ya existe? Puedes contestarlo ahora o dejar que el paso 3 lo saque con preguntas.
- Stack. No se decide hasta el paso 4, pero si ya tienes preferencia (por ejemplo .NET, Node, Python) dímelo cuando lleguemos ahí.

Cuando digas "siguiente", inicializo git y corremos el paso 1 con la constitución.