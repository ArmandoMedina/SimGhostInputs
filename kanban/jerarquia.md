# La jerarquía QUÉ / CÓMO — dos sombreros y un puente

> El QUÉ (producto) y el CÓMO (ingeniería) se separan a propósito: **quien define qué hace el sistema no tiene que saber cómo se construye, y viceversa.** Heredado del andamio del linaje (ADR [0004](../docs/decisions/0004-centralizacion-del-conocimiento.md)); mapea a marcos profesionales (DDD, C4, arc42, Diátaxis, MADR) — no es invento.

## Los dos sombreros

- **QUÉ y PORQUÉ** — sombrero de Producto. Vive en `product/`: qué debe hacer el sistema, descrito por comportamiento, nunca por implementación.
- **CÓMO** — sombrero de Ingeniería. Vive en `engineering/` + el código: qué pieza real lo soporta y cómo se implementa.
- **El puente entre ambos son los ADR** (`docs/decisions/`): cada decisión que cruza de un lado al otro queda registrada con su porqué.

## La jerarquía del QUÉ — 5 niveles

De lo amplio a lo atómico, cada nivel responde una pregunta:

| Nivel | Pregunta que responde |
|---|---|
| **Ecosistema** | ¿En qué universo vive esto? (telón de fondo, rara vez una nota) |
| **Producto / Solución** | ¿Qué cosa entrega valor y se puede nombrar? (normalmente un repo = un producto) |
| **Dominio** | ¿Qué área de responsabilidad coherente? — define alcance y **fuera de alcance** |
| **Módulo** | ¿Qué pieza funcional dentro del dominio? (agrupa capacidades) |
| **Capacidad** | ¿Qué puede hacer el sistema, **exactamente**? |

La **capacidad es la unidad atómica**: se describe por comportamiento + criterios de aceptación en Gherkin (`Dado que… cuando… entonces…`), nunca por implementación. Una capacidad no se revisa aislada — siempre contra su módulo, su dominio y su alcance.

Del lado del CÓMO, tres tipos de nota se conectan a las capacidades: el **componente del sistema** (¿qué pieza real lo soporta? — BD, API, plataforma), la **especificación técnica** (¿cómo se implementa una capacidad concreta?) y el **modelo de datos** — con la distinción del linaje: la tabla es *la alacena* (qué se guarda, `TBL-<ORIGEN>-<NN>`) y la spec es *la receta* (cómo se llena). Cada nota lleva su `estado:` — el ciclo de vida completo vive en [`estados.md`](estados.md).

## Claves estables de trazabilidad

Módulos, capacidades y specs llevan una `clave:` en su frontmatter que **no cambia al renombrar**: `FAM-MOD` (módulo), `FAM-MOD-NN` (capacidad, hereda el prefijo de su módulo), `TEC-<ORIGEN>-NN` (spec). Los cambios se propagan por el grafo usando la clave, no el título.

## Cómo vive en disco (las convenciones del grafo)

- **Formato híbrido de enlaces:** links markdown inline (GitHub navega) + una sección `## Relacionado con` al pie con `[[wikilinks]]` (Obsidian teje el grafo). No es redundancia: cada una sirve a una superficie distinta — el mismo git se lee desde GitHub, VS Code y Obsidian.
- **Carpetas planas por tipo; la jerarquía vive en el grafo.** Anidar carpetas es rígido y lo transversal no tiene hogar único: el nivel lo dice el frontmatter y los enlaces, no la ruta.
- **Diagramas en Mermaid por defecto** (texto, diffeable, rinde nativo en GitHub y Obsidian); formatos binarios solo para lo que Mermaid no alcanza.
- **Un glosario como SSOT del vocabulario:** un término, un significado, el mismo nombre en todos los docs. Si renombras algo, búscalo en el resto antes de cerrar el cambio. Y el límite anti-duplicación: vocabulario de negocio en el glosario; campos y tablas técnicas en su componente dueño, solo enlazados. *Si dos áreas usan el término distinto, el conflicto es real y se resuelve — no se documentan dos versiones.*

## Las reglas de oro

- **Define el comportamiento para que cualquiera implemente sin inventar reglas de negocio.** Lo ambiguo se **marca**, no se inventa.
- **Regla de negocio ≠ criterio de aceptación.** La regla dice *qué es verdad*; el criterio dice *cómo lo pruebas*.
- **¿Dónde va cada cosa?** Ante la duda de nivel, **sube uno**.

## Mapa a marcos profesionales

Nada de esto es invento; cada pieza reconoce su linaje profesional — para que quien llegue del gremio reconozca la forma:

| Pieza de Jidoka | Marco |
|---|---|
| Jerarquía QUÉ/CÓMO | Espacio-problema vs espacio-solución; [DDD](https://martinfowler.com/bliki/DomainDrivenDesign.html) + [C4](https://c4model.com/) |
| Glosario | Ubiquitous Language (DDD); [arc42 §12](https://docs.arc42.org/section-12/) |
| Procesos (runtime) | [arc42 §6](https://docs.arc42.org/section-6/) |
| ADRs | [MADR](https://adr.github.io/madr/); arc42 §9 |
| Organización de la doc | [Diátaxis](https://diataxis.fr/) |

## Dónde está el ejemplo vivo

Esta jerarquía corre en producción en el repo más maduro del linaje (caso interno: 22 capacidades, 14 módulos, 9 dominios, con un auditor determinista del grafo que valida frontmatter, wikilinks y Gherkin de las capacidades vigentes). Las plantillas y el auditor llegan al kit en los Sprints 2-3 ([ROADMAP](../ROADMAP.md)); el conocimiento no espera a la máquina.
