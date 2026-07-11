# Ledger de verificación de citas ancla

Verificación adversarial contra fuente primaria, 2026-07-04, por agentes independientes con la
instrucción de REFUTAR cada afirmación. Ante discrepancia con el chat fuente (el corpus interno
del linaje, no publicado — ver la nota en `decisiones/README.md`), manda este ledger.

## Frente 1 — IA / software (verificado 2026-07-04)

| # | Afirmación | Veredicto | Corrección |
|---|---|---|---|
| 1 | Issue anthropics/claude-code #40117: Opus 4.6 burla hooks (`--no-verify`, `git stash`, flags silenciosos), 6 commits 27-mar-2026, hasta 63 tests fallando, pese a reglas deny | **VERIFICADO** | Además: tergiversó lo hecho al ser cuestionado (más fuerte que lo citado) |
| 2 | arXiv 2604.14228 "Dive into Claude Code": 1.6% lógica IA / 98.4% infraestructura | **VERIFICADO (matiz)** | Es estimación de "community analysis" reportada en §3.1, no medición del paper |
| 3 | Chroma "Context Rot" (Hong, Troynikov, Huber): 18 modelos, cae en tareas triviales | **VERIFICADO** | jul-2025 |
| 4 | Xander Jiao: poka-yoke por nombre + 0.95^10 ≈ 59.87% | **VERIFICADO** | Fecha exacta 27-ago-2025 |
| 5 | arXiv 2408.02205 Swiss Cheese guardrails "de James Reason" | **PARCIAL** | Título vigente (v4): "Swiss Cheese Model for AI Safety: A Taxonomy and Reference Architecture..."; NO cita a Reason (cita Shabani et al. 2024) |
| 6 | npj Digital Medicine 2026 "Flight rules for clinical AI" | **VERIFICADO** | vol. 9, art. 201, 31-ene-2026; Bainbridge ref. 25; "digital copilot"/"pilot-in-command" textuales |
| 7a | Required reviewer rule GA 17-feb-2026 (GitHub) | **VERIFICADO** | — |
| 7b | "Cierre definitivo" de aprobación de PRs por Actions, anunciado 7-nov-2025 | **NO VERIFICADO — FALSO** | El changelog de esa fecha trata de `pull_request_target`/environments. La restricción del GITHUB_TOKEN data de 2022 y sigue siendo toggle de admin |

## Frente 2 — Calidad / gobernanza / oversight (verificado 2026-07-04)

| # | Afirmación | Veredicto | Corrección |
|---|---|---|---|
| 1 | Deming punto 3, redacción exacta | **VERIFICADO** (deming.org) | — |
| 2 | Goodhart 1975 + frase popular de Strathern 1997 | **VERIFICADO** | Strathern verificada en PDF primario (p. 308); el paper de Goodhart 1975 no se pudo abrir directo (confirmado vía fuentes académicas concordantes) |
| 3 | Campbell's Law, redacción exacta | **VERIFICADO** (PDF primario 1976, p. 49) | Campbell lo llama "pessimistic laws" (plural) |
| 4 | Vaughan 1996, normalization of deviance / Challenger | **VERIFICADO** | — |
| 5 | Elish 2019 "moral crumple zone", cita textual | **VERIFICADO** (ESTS vol. 5) | — |
| 6 | Green 2022: ~40 políticas + cita "false sense of security" | **PARCIAL** | Son **41** políticas; la cita es textual |
| 7a | Overrides de alertas EHR 49%-96% | **PARCIAL** | El rango es de **van der Sijs et al. 2006 (JAMIA)**, no del primer de AHRQ (que solo dice "vast majority") |
| 7b | Joint Commission SEA #50: 98 eventos, 80 muertes, 85-99% sin intervención | **VERIFICADO** (PDF) | Fecha exacta: 8-abr-2013 |
| 8 | Koppel 2008: 15 workarounds, 31 causas | **VERIFICADO** | — |
| 9 | Schneier acuñó "security theater" en Beyond Fear 2003 | **PARCIAL** | La cita usada era la definición de Wikipedia. Frase del libro: "some countermeasures provide the feeling of security instead of the reality. These are nothing more than security theater." |
| 10 | Choi/Hecht/Tayler 2012, surrogation, incentivos la exacerban | **VERIFICADO** | — |

## Frente 3 — Aviación / factores humanos (verificado 2026-07-04, segunda corrida)

| # | Afirmación | Veredicto | Corrección |
|---|---|---|---|
| 1 | SAFO 13002 (4-ene-2013): "continuous use... does not reinforce a pilot's knowledge and skills in manual flight operations" | **VERIFICADO** | Textual: "Unfortunately, continuous use of **those systems** does not reinforce..." (antecedente: autoflight systems). PDF de la FAA da 403; cotejado contra copia íntegra |
| 2 | Bainbridge 1983: 3 citas verbatim | **VERIFICADO** (contra el PDF completo) | (a) inicia "The second irony is that..."; (c) el original dice "**his** task", no "their task"; (b) exacta, precedida de "Perhaps the final irony is that" |
| 3 | Billings 1996: in command / involved / informed / predictable / monitoreo mutuo | **NO VERIFICADO textualmente** | Metadatos confirmados (NASA-TM-110381, feb 1996); el PDF primario excede el límite del fetcher. Consistente con secundarias → tratar como paráfrasis fiel, no citar entre comillas |
| 4 | Parasuraman & Manzey 2010: complacency (monitoreo) vs bias (omisión/comisión) | **VERIFICADO** | Human Factors 52(3):381-410; definiciones confirmadas en abstract |
| 5 | Sheridan & Verplank 1978: escala de 10 niveles | **PARCIAL** | La escala existe (Tabla 8.2, p. 8-17, confirmada en escaneo DTIC) pero sin texto verbatim extraíble; el wording del nivel 10 "ignorando al humano" es de Parasuraman-Sheridan-Wickens 2000 — citar la escala vía el paper del 2000 |
| 6 | Children of the Magenta: VanderBurgh ~1997, 68% | **PARCIAL** | Primaria = video (no consultable). Secundarias consistentes: abril 1997; 68% de accidentes, **incidentes y violaciones** por mala gestión de automatización |
| 7 | AF447 (BEA jul-2012) y Asiana 214 (NTSB AAR-14/01) | **VERIFICADO (matices)** | BEA confirmado, incl. textual "an absence of training, at high altitude, in manual aeroplane handling". NTSB: probable cause y FLCH→HOLD confirmados; "FLCH trap" es apodo coloquial, no del informe; la falta de vuelo manual se trata vía entrenamiento/política, no como frase literal |
| 8 | TIP: ~2% prevalencia, 80-90% hit rate, remedial, 34% poco realistas (Sensors 2022) | **PARCIAL** | Autores reales: **Riz à Porta, Sterchi y Schwaninger** (no Hättenschwiler/Mendes). 34%, 80-90% (estudio: 88%) y reentrenamiento remedial confirmados textuales. La prevalencia ~2% NO aparece en ese artículo — queda sin fuente primaria |

**Balance global de los 3 frentes (~25 afirmaciones):** 1 falsa (aprobación de PRs por Actions,
frente 1), 1 no verificable textualmente (Billings), 8 parciales con correcciones de atribución
o wording, el resto verificadas — varias contra el PDF primario completo.

## Pruebas de vida (muestreo contra fuente viva)

El ledger no se pudre solo por errores nuevos: también porque las fuentes se mueven (disparo
*prueba-de-vida-del-gate*, aplicado a la doctrina misma). Registro de muestreos:

| Fecha | Muestra | Resultado |
|---|---|---|
| 2026-07-09 | 5 citas ancla: Deming punto 3 (deming.org), arXiv 2408.02205 (título v4), Chroma "Context Rot" (autores, 18 modelos, degradación en tareas triviales), Elish 2019 (ESTS vol. 5, "moral crumple zone"), Parasuraman & Manzey 2010 (Human Factors 52(3):381-410, complacency vs bias) | **5/5 vivas** y consistentes con el veredicto registrado. Nota: el reporte de Chroma se mudó de `research.trychroma.com` a `trychroma.com/research/context-rot` (301); la cita no cambia |
