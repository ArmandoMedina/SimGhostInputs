# Disparos — doctrina compilada a mensajes de gate

Fragmentos listos para pegarse en hooks (`permissionDecisionReason`, `Stop` hooks), mensajes de
CI y templates de PR. Regla de formato: **la regla + el porqué, en 2-4 líneas, autocontenido** —
el mensaje llega en el momento del disparo y no puede asumir que la IA leyó nada más.
(ADR 0003: la IA no lee docs de metodología; este es el único formato en que la doctrina le llega.)

## Catálogo v0

### anti-memoria
> Nada de memorias: todo al repo. Lo que ibas a guardar tiene un lugar con dueño: estado en vuelo
> a HANDOFF.md; una decisión y su porqué a docs/decisions/ (un ADR, listado en su índice); hechos
> del dominio a los docs del dominio del repo; recursos externos a docs de recursos. Esta regla se
> cablea porque repetirla en prosa falló.

### evidencia-no-palabra
> Un veredicto sin artefacto no vale. El gate lee el artefacto (archivo, timestamp, diff, log de
> corrida), no la palabra del agente. Si afirmas que probaste algo, la evidencia debe existir en
> disco antes de cerrar.

### no-verify-es-teatro
> No uses --no-verify ni manipules el estado staged para pasar un hook. Caso documentado: un
> agente lo hizo 6 commits seguidos con tests fallando y tergiversó lo hecho (issue #40117 de
> claude-code). El muro real es el required check server-side; saltarte el hook local solo
> pospone y agranda el fallo.

### click-it-down
> Si la tarea se complica o el resultado te sorprende, BAJA el nivel de automatización: de
> hacerlo end-to-end, a proponer y esperar aprobación humana paso a paso. No pelees dentro del
> modo automático mientras la situación se degrada (doctrina Children of the Magenta).

### decision-queda-en-humano
> Automatiza alto la adquisición y el análisis (reunir evidencia, resumir, buscar); mantén baja
> la decisión y la ejecución: propone, el humano elige y firma. Subir el nivel en la etapa de
> decisión fabrica sellos de goma (LOA de dos ejes, Parasuraman-Sheridan-Wickens 2000).

### deny-vs-ask
> deny (bloqueo duro, estilo Airbus) para lo irreversible y peligroso; ask con override (estilo
> Boeing) para lo que requiere juicio humano. Mezclar filosofías por tipo de acción, no elegir
> una sola.

### prueba-de-vida-del-gate
> ¿Cuándo fue la última vez que este gate rechazó algo real? Si la respuesta es nunca, el gate
> está podrido aunque el tablero esté verde. Un gate sano genera fricción visible; uno podrido,
> silencio.

### desconfia-de-la-compactacion
> Los resúmenes de compactación pueden mentir. Antes de retomar algo resumido, verifica contra
> el artefacto real (código, archivo, fuente primaria) — no contra el resumen.

### prueba-de-humo-del-gate
> Un gate nuevo no se estrena sin correrlo contra el artefacto real. La primera corrida real
> caza bugs del propio gate y confirma que bloquea lo que debe (caso de campo: cazó un bug del
> parser y bloqueó un artefacto desactualizado en la misma corrida). Quien valida también se
> valida.

### excepciones-cableadas
> Si el negocio tiene una excepción legítima a un check (un valor negativo normal, un literal
> a mano esperado), cabléala EXPLÍCITA y con nombre en el gate. La excepción tolerada en
> silencio o hace gritar al gate en falso (fatiga, disuse) o lo afloja para todos.

### frontera-nda
> Las lecciones del trabajo cruzan a repos/notas personales SOLO a nivel método, anonimizadas:
> nunca nombres de clientes, empleados, procesos, montos, proveedores, canales ni repos del
> trabajo. Cita "caso N"; los detalles viven en el repo del trabajo, del lado correcto del NDA.

### capacita-desde-el-artefacto
> Cuando expliques o capacites al humano, ancla la lección al artefacto versionado (señala el
> doc/runbook/ADR), no a tu memoria de modelo. La capacitación improvisada es output de IA:
> falible. Los dos pájaros comen del mismo comedero — los artefactos durables.
