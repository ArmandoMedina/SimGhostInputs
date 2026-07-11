# 06 — Fronteras: qué es reclamable y qué se cita

Resultado de la búsqueda deliberada de originalidad (2026-07-04). La honestidad exige distinguir
tres categorías. La ventana se está cerrando: el espacio "manufactura→agentes" se está poblando
rápido en 2026.

## Reclamable (nadie lo ha escrito integrado)

1. **La síntesis poka-yoke como lente unificadora.** Las piezas existen sueltas: Xander Jiao
   (27-ago-2025 [VERIFICADA]) mapeó semiconductor yield → agentes y menciona poka-yoke *como una
   técnica en una lista* (más el argumento multiplicativo: 0.95^10 ≈ 59.87% de éxito en 10 pasos);
   un paper de arXiv (2408.02205 [VERIFICADA con matiz: título actual "Swiss Cheese Model for AI
   Safety..."; no cita a Reason directamente]) usa el Swiss Cheese para guardrails multicapa.
   **Pero nadie une** poka-yoke/Toyota + "verifica el artefacto, no la palabra" + los dolores
   (amnesia / context rot / compactación que miente) + hooks deterministas **como un mismo linaje
   de ingeniería de calidad**. El vínculo explícito "hook de Claude Code = poka-yoke físico" está
   a un paso y nadie lo da.

2. **El capture-test tipo TIP para revisores humanos de IA.** Prácticamente vacío: ningún sistema
   en producción, ningún framework, ninguna propuesta madura peer-reviewed. Solo la analogía
   (madura en aeropuertos), un piloto de radiología exploratorio (arXiv 2412.12042) y heurísticas
   indirectas. Construirlo u escribirlo es frontera genuina.

3. **TEM para IA** (Threat & Error Management). La pieza de aviación *menos* transferida: aparece
   implícita en co-teaming y "two-factor judgment", pero nadie ha portado el marco completo
   (amenazas / errores / estados no deseados, con capas de detección) a agentes como marco propio.

4. **La tesis dual del costo de dignidad.** "La disciplina se pone donde no hay costo de dignidad
   —el robot— y desde ahí habilita al humano a seguir siendo humano." El traslado del costo de la
   rigidez del humano a la máquina, como resolución de la tensión histórica de la ingeniería de
   calidad (Deming 8/12, respeto por las personas de Toyota), no está articulado por nadie.

## Prestado y maduro (citar, no reclamar)

- **"Verify don't trust / el control fuera del modelo"** — casi ortodoxia entre practicantes
  2025-2026 (ACM Queue "Guardians of the Agents"; GitHub Blog; Microsoft "The Gate Is the
  Product"; Mneme "verificas el diff").
- **El paralelo aviación→IA** — ya reclamado: npj Digital Medicine 2026 "Flight rules for
  clinical AI" [VERIFICADA] (Bainbridge, magenta line, práctica mínima sin IA, "digital copilot",
  pilot-in-command); NASA CRM-A (2018).
- **Context rot** — con research formal: Chroma, "Context Rot: How Increasing Input Tokens
  Impacts LLM Performance" (Hong, Troynikov, Huber, jul-2025 [VERIFICADA]; 18 modelos; la
  fiabilidad cae incluso en tareas triviales).
- **La crítica a la supervisión decorativa** — Elish 2019, Green 2022, automation bias empírico
  (todo verificado, ver `04-como-se-pudre.md`).
- **El dato empírico del scaffolding**: "Dive into Claude Code" (arXiv 2604.14228 [VERIFICADA con
  matiz]) — ~1.6% del código de Claude Code es lógica de decisión IA, 98.4% infraestructura
  operacional. OJO al citar: el paper lo reporta como estimación de *community analysis*, no como
  medición propia.

## Corregido (no citar la versión del chat)

- ~~"GitHub cerró definitivamente la aprobación de PRs por Actions el 7-nov-2025"~~ — **FALSO**.
  El changelog real de esa fecha trata de `pull_request_target` y environment branch protections.
  La restricción de que el GITHUB_TOKEN apruebe PRs es un default desactivado **desde 2022** y
  sigue siendo un toggle de administrador. La implicación de diseño se mantiene (desactivar ese
  toggle es parte de configurar bien el muro), pero el "cierre definitivo 2025" no existió.

## Qué hacer con la ventana

Si se publica, el orden de valor es: (1) el ensayo de la síntesis poka-yoke (la lente
unificadora, con los tres linajes y los dolores atados a los gates), (2) el diseño del
capture-test TIP-para-IA como propuesta concreta, (3) TEM-para-IA como marco. Los tres se apoyan
en este repo tal cual; falta solo la pasada de verificación de aviación y redacción final.
