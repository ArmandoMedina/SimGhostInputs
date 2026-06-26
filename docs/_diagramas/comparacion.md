# Comparación de diagramas del flujo de trabajo (SCRATCH)

> Archivo **temporal** para comparar las opciones visualmente. **NO** es parte de la
> documentación oficial. Cuando elijas, la ganadora se integra a `flujo-de-trabajo.md`
> y esta carpeta `_diagramas/` se borra.
>
> **Cómo verlo renderizado:** abre este archivo en **Obsidian** (o VS Code → "Open Preview",
> `Ctrl+Shift+V`). El SVG ábrelo en **navegador / VS Code / Obsidian** (Windows Fotos no
> renderiza SVG y dice "inválido" — no es que el archivo esté roto).
>
> Versiones con **más detalle, en el punto de equilibrio**: fase Explorar→¿se queda?, rama de
> decisión→ADR, qué atrapa cada check, los 2 jobs del CI, las skills que asisten, la
> precondición del hook y el escape `--no-verify`, la frontera de versión, branch protection y
> el límite semántico.

---

## Opción B — Mermaid (texto-en-repo, se renderiza en Obsidian / GitHub / VS Code)

```mermaid
flowchart TD
    A(["Explorar<br/>rama suelta · nada corre"]) --> D{"¿se queda?"}
    D -->|"no, sigo probando"| A

    subgraph J["JUICIO · aconseja (antes de subir)"]
        D -->|"sí = commit"| B["Consolidar el cambio + su test"]
        B --> DEC{"¿fue decisión?"}
        DEC -->|sí| ADR["registrar ADR<br/>skill adr-helper"]
        DEC -->|no| RV["/code-review<br/>IA · aconseja, no bloquea"]
        ADR --> RV
    end

    RV --> C{"git push"}
    SET["1 vez: git config core.hooksPath .githooks"] -.- C
    SKP["escape: git push --no-verify"] -.- C

    subgraph L["LOCAL · avisa — hook pre-push ▶ verificar.ps1 (sale 0)"]
        C --> K1["ruff check<br/>imports y vars sin usar"]
        C --> K2["ruff format --check<br/>estilo canónico"]
        C --> K3["pytest<br/>lógica del motor"]
        C --> K4["doc-gate<br/>CHANGELOG + checklist"]
    end

    K1 & K2 & K3 & K4 --> P[("GitHub · origin/master")]

    subgraph N["NUBE · bloquea — CI tests.yml (sale ≠0 si falla)"]
        P --> JL["job lint (Ubuntu)<br/>ruff check + format --check"]
        P --> JP["job pytest (Windows)<br/>3.10 · 3.11 · 3.12"]
        JL --> V{"¿todo verde?"}
        JP --> V
    end

    V -->|sí| OK(["queda en master"])
    V -->|no| X(["arregla y repite"])
    X -.->|corrige y re-push| C
    OK -.->|"ocasional · skill release-helper"| REL["versión vX.Y.Z"]
    P -. "futuro: branch protection = bloquea merge a colaboradores" .-> N
    OK -.->|"lo visual NO lo cubre ninguna barrera"| QA["QA manual con video real<br/>HUD · overlay · sync"]

    classDef avisa fill:#fef9c3,stroke:#ca8a04,color:#111
    classDef bloquea fill:#fee2e2,stroke:#dc2626,color:#111
    classDef ok fill:#dcfce7,stroke:#16a34a,color:#111
    classDef juicio fill:#eff6ff,stroke:#2563eb,color:#111
    classDef manual fill:#f1f5f9,stroke:#64748b,color:#111
    classDef nota fill:#ffffff,stroke:#94a3b8,color:#475569
    class K1,K2,K3,K4 avisa
    class JL,JP,V bloquea
    class OK ok
    class RV,ADR juicio
    class QA manual
    class SET,SKP nota
```

---

## Opción C — BPMN formal (imagen SVG)

Notación BPMN con carriles, evento inicio/fin ◯◉, gateways ◇, los 2 jobs del CI, qué atrapa
cada check, notas de precondición/escape, leyenda y el callout del límite semántico.

![Flujo en notación BPMN](flujo-bpmn.svg)

---

## Resumen

| | Bonito | Texto en repo | Aguanta detalle | Drift |
| :-- | :-- | :-- | :-- | :-- |
| **B — Mermaid** | diagrama con color | sí | mucho (auto-acomoda) | ninguno |
| **C — BPMN/SVG** | notación pro, nítido | imagen (binario) | medio (se acomoda a mano) | sí |

**Recomendación:** **Mermaid (B)** como diagrama canónico en `flujo-de-trabajo.md`; **SVG (C)**
además como "portada" visual si te gusta más vistoso (binario, se mantiene a mano).
