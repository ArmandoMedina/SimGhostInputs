# 03 — Aviación: el único campo que vivió el dilema del pájaro 2 a escala, con muertos

La aviación enfrentó exactamente esto: una automatización muy capaz que desplaza al humano,
pero el humano tiene que seguir siendo el árbitro final. No lo "resolvió" — lo convirtió en
**riesgo gestionado** con cuatro movimientos: (1) obligar a practicar el modo manual en calma,
(2) mantener al humano como supervisor *activo*, no monitor pasivo, (3) hacer la automatización
transparente en su modo e intención, (4) dosificar la autoridad de la automatización por etapa
y riesgo.

> Citas verificadas contra fuente primaria (2026-07-04, ver `citas-verificadas.md` frente 3).
> Correcciones aplicadas abajo. Excepción: los principios de Billings quedaron como paráfrasis
> fiel (el PDF primario no fue accesible) — no citarlos entre comillas.

## La columna teórica (por qué el pájaro 2 es peligroso)

- **Bainbridge, "Ironies of Automation" (Automatica 19(6), 1983)** [VERIFICADAS verbatim contra
  el PDF] — enunció el problema hace 40 años: *"By taking away the easy parts of his task,
  automation can make the difficult parts of the human operator's task more difficult"* (p. 777);
  y la ironía final: *"it is the most successful automated systems, with rare need for manual
  intervention, which may need the greatest investment in human operator training"* (p. 777). → **Mientras mejor sea la IA, MÁS hay que invertir en mantener vivo el
  juicio del humano** — lo contrario de lo que dicta la intuición y el presupuesto.
- **Endsley & Kiris (1995), out-of-the-loop performance problem** — el monitor pasivo pierde
  situation awareness nivel 2 (qué significan los datos) y reacciona lento y peor cuando debe
  intervenir. "Poner un humano a mirar" no basta.
- **Parasuraman & Manzey (2010)** — los dos modos de falla del gate humano con nombre:
  **complacency** (deja de revisar porque casi siempre acierta — falla de monitoreo) y
  **automation bias** (defiere a la máquina contra su propio juicio — falla de decisión, con
  errores de omisión y de comisión).
- **Billings (NASA-TM-110381, feb 1996), Human-Centered Automation** — el humano debe estar
  **in command, involved, informed**; la automatización debe ser **predecible**; monitoreo mutuo.
  [Paráfrasis fiel; el PDF primario no fue verificable textualmente — no citar entre comillas.]

## Los accidentes-lección

- **AF447 (2009)** [VERIFICADO contra el documento del BEA] — EL caso de deskilling: pitots
  congelados → autopiloto se desconecta → stall no identificado hasta el mar. Entre los factores,
  textual del BEA: *"an absence of training, at high altitude, in manual aeroplane handling"*.
  La primera vez que vuelas a mano no puede ser la emergencia.
- **Asiana 214 (2013)** [VERIFICADO, NTSB AAR-14/01] — over-reliance + confusión de modo: la
  selección de FLCH SPD llevó el autothrottle a HOLD, "a mode in which the A/T does not control
  airspeed", y nadie lo sabía ("FLCH trap" es el apodo coloquial, no términos del informe).
  Confiar en un sistema que no entiendes en detalle falla por los modos silenciosos que asumiste
  cubiertos.
- **Tenerife (1977) / United 173 (1978)** — origen del CRM: el subordinado con la información
  correcta que no logra frenar al superior (authority gradient).

## Las doctrinas, mapeadas

| Doctrina | Prescribe | Traducción a humano-IA |
|---|---|---|
| SAFO 13002/17007 (FAA, 2013/17) — manual proficiency | el uso continuo de la automatización no refuerza las habilidades manuales → práctica manual deliberada, en condiciones benignas | casos de bajo riesgo resueltos **sin IA a propósito**, programados; no esperar a que el límite/outage te fuerce en el peor momento |
| "Children of the Magenta" (VanderBurgh, AA ~1997) | cuando la situación se complica, **baja el nivel de automatización** ("click it down"), no pelees dentro del modo automático | graduar: IA end-to-end → IA propone/humano aprueba → humano a mano, según riesgo |
| CRM — challenge & response, authority gradient | el subordinado tiene el **deber** de cuestionar; Pilot Monitoring es rol activo | el humano debe contradecir a la IA; ojo con el gradiente invertido (la IA suena fluida y segura → el humano no la cuestiona) |
| Sarter & Woods — automation surprises / mode confusion | feedback del **modo/estado**, no solo del resultado ("what is it doing now?") | la IA expone su razonamiento y en qué modo está (investigando vs afirmando), no solo la respuesta pulida |
| TEM (Helmreich) — Threat & Error Management | los errores **ocurrirán**; gestión por capas de detección/mitigación | Swiss cheese operativo: capas que atrapan el error antes del estado irreversible |

## Las dos palancas de diseño concretas

**1. LOA de dos ejes (Parasuraman, Sheridan & Wickens, 2000).** La automatización tiene cuatro
etapas — adquirir información, analizar, **decidir**, ejecutar — y cada una admite su propio
nivel (escala de 10 niveles; existe en Sheridan-Verplank 1978, Tabla 8.2, pero el wording
citable de los niveles es el del paper del 2000 — citar la escala vía ese paper). Receta:

> Automatiza ALTO adquisición y análisis (la IA reúne evidencia, resume, busca). Mantén BAJO
> decisión y ejecución (la IA sugiere, el humano elige y firma — niveles 4-5). El pecado mortal
> es subir el nivel en la etapa de **decisión** hasta donde el humano solo veta o ni se entera
> (niveles 6-10). Ahí nace el sello de goma.

**2. Airbus vs Boeing = prevención vs detección.** Airbus: límites **duros** (la automatización
impide cruzar el envelope; el piloto no puede anular) = gate que bloquea = `deny`. Boeing:
límites **blandos** (avisa y frena, pero el piloto puede anular) = gate que avisa = `ask` +
override. Regla práctica: **`deny` para lo irreversible y peligroso; `ask` con override para lo
que requiere juicio** — y Boeing solo funciona si se combate el automation bias con cross-check
obligatorio. Mezclar filosofías, no elegir una.

## El caso del límite de suscripción

Un límite de tokens que te tira a modo manual es un forcing function real (externo, no saltable)
pero **con el timing de AF447**: se dispara justo en alta carga, con la mano fría, y por azar —
no construye proficiency, solo expone su ausencia. La respuesta de la doctrina: institucionaliza
la práctica manual en calma ANTES (SAFO 13002), y el corte se vuelve un no-evento. Nota de
convergencia: el corte solo es sobrevivible porque el estado vive en artefactos durables
(anti-amnesia) — el humano retoma desde el disco, no desde una cabeza de IA apagada.

## Honestidad sobre originalidad

El paralelo aviación→IA **ya está reclamado y va rápido**: npj Digital Medicine (2026), "Flight
rules for clinical AI" [VERIFICADA: vol. 9, art. 201, 31-ene-2026; cita a Bainbridge y children
of the magenta; propone práctica mínima sin IA y el reencuadre autopiloto → "digital copilot" con
el humano como pilot-in-command]; NASA CRM-A (2018). **Citar, no reclamar.** El hueco que sí
sigue abierto: **TEM para IA** (ver `06-fronteras.md`).
