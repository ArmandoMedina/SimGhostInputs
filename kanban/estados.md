# Estados y prioridades — el ciclo de vida de una nota

> El vocabulario que los gates modulan. Sin esto, "auditor modulado por estado" (Sprint 2) es una frase sin referente. Heredado del andamio del linaje (ADR [0005](../docs/decisions/0005-exprimido-final-del-linaje.md)).

## Dos ejes independientes

- **Estado** = madurez de la **definición**: `en_definicion → en_revision → vigente`, más los laterales `pausado` y `fuera_de_alcance`.
- **Prioridad** = **valor** (MoSCoW: Must/Should/Could/Won't) más `Por definir`.

Una nota puede ser `vigente` y Won't Have; otra `en_definicion` y Must. Los ejes no se mezclan.

> **`vigente` NO significa construido.** Significa *definición aceptada para este corte*. Lo construido lo dice el código y sus tests, no el frontmatter.

**Regla dura:** una nota `pausado`, `fuera_de_alcance` o Won't Have **no se trata como capacidad activa** — ni se implementa, ni se audita como faltante.

## Las ambigüedades se cazan, no se inventan

Palabras como *"cuando aplique"*, *"suficiente"*, *"configurable"*, *"autorizado"* son decisiones disfrazadas de adjetivos. La regla: **márcalas como pendiente, no las inventes** — quien define es el cliente, no el redactor.

Al auditar documentación, los hallazgos se separan en 6 categorías: ambigüedad · contradicción · hueco (falta la regla) · duplicado (dos docs dueños del mismo hecho) · desactualizado · roto (link/clave).

## El gate se modula por estado

Los gates disparados por **documentación** escalan con el `estado:` de la nota:

| Estado | Qué exige el gate |
|---|---|
| `en_definicion` / `en_revision` | Solo consistencia documental (frontmatter, links) |
| `vigente` | Criterios de aceptación presentes; test faltante **avisa** (vigente ≠ implementado) |
| `pausado` / `fuera_de_alcance` | Nada |

Los gates disparados por **código NO se modulan** — el diff ya es la señal de implementación. Y dos reglas de diseño: **no se inventa un estado `implementado`** (duplicaría el vocabulario: eso ya lo dicen los tests); si el gate **no puede leer** la ruta, degrada a no-marcar — *nunca un falso bloqueo*.

## Gobernanza documental (solo arquetipo regulado)

Para repos doc-only/regulados, un documento además madura en 3 estados: **borrador → referencia → oficial**. "Oficial" exige *quién aprobó y cuándo*, más el tag de versión. La frase que lo funda:

> **Versionar en git da trazabilidad, pero no sustituye una aprobación formal donde el riesgo lo exige.** Un commit no es una firma.

En un proyecto personal, esta capa se borra sin culpa (menú, no molde). Cuidado clásico: taggear `v1.0.0` con firmas pendientes.
