# 01 — Linaje: manufactura, calidad y ciencia de la seguridad (1896–2009)

Un solo axioma atraviesa ~130 años: el enfoque **"persona"** (culpar, entrenar, pedir disciplina)
falla porque el actor es intrínsecamente falible; el enfoque **"sistema"** (barrera determinista
externa que hace el error imposible o lo atrapa en la fuente) funciona.

| Fuente | Actor falible | Gate determinista fuera del actor | Equivalente en gobierno de IA |
|---|---|---|---|
| Poka-yoke (Shigeo Shingo, años 60, TPS) | operario que olvida un paso | pieza que no encaja / paso que no avanza | hook `PreToolUse` deny: el error se vuelve imposible, no desaconsejado |
| Jidoka + Andon (Sakichi Toyoda 1896 → TPS) | operario que no puede vigilar todo | la máquina se detiene sola ante el defecto; cualquiera para la línea | `Stop` hook que frena el cierre de sesión ante defecto |
| Deming / SPC (1950–1982) | inspector final | calidad construida y medida en la fuente | required check > "la IA dice que pasa"; validar en el flujo, no al final |
| Swiss Cheese (James Reason, 1990/2000) | humano al que se le pide esforzarse más | capas de defensa cuyos agujeros no deben alinearse | ventanas de validación superpuestas (working tree / commit / CI) |
| Checklist (B-17 1935; Gawande/OMS 2007-09) | memoria del experto | ritual forzado + evidencia registrada | gate de evidencia fresca: el hook lee el artefacto, no la palabra |
| Forcing functions (Don Norman, 1988) | usuario que puede equivocarse | interlock/lockout que impide el mal uso | un fallo en la etapa N impide la etapa N+1 |

## Los conceptos, en corto

- **Poka-yoke** (Shingo): los *errores* humanos son inevitables; los *defectos* ocurren solo cuando
  el error llega al cliente. Distinción clave: poka-yoke de **prevención** (hace el error
  físicamente imposible — el conector que solo entra en una orientación) vs de **detección**
  (lo atrapa apenas ocurre y alerta). Mapea directo a `deny` vs `ask`/warning.
- **Jidoka / Andon**: "automatización con toque humano". El telar de Toyoda (1896) se detenía solo
  al romperse un hilo, para no seguir tejiendo defectos. Filosofía: *build quality in, don't
  inspect it in* — el defecto no se propaga porque el sistema mismo se frena.
- **Deming, punto 3 de los 14** [VERIFICADA verbatim]: *"Cease dependence on inspection to achieve
  quality. Eliminate the need for inspection on a mass basis by building quality into the product
  in the first place."* La inspección final es tardía, cara e ineficaz.
- **James Reason** — la distinción central de la ciencia de seguridad moderna: **person approach**
  (culpar/exhortar → falla) vs **system approach** (rediseñar condiciones → funciona). Cita ancla:
  *"We cannot change the human condition, but we can change the conditions under which humans
  work."* (BMJ, 2000). El hallazgo del laboratorio de campo ("repetírselo no funcionó, hubo que cablearlo") es esta
  distinción redescubierta desde el dolor.
- **Checklists**: nacen del crash del Boeing Model 299/B-17 (1935, "too much airplane for one man
  to fly") — la respuesta no fue más entrenamiento sino una checklist. Gawande (2009): en dominios
  complejos el fallo no viene de ignorancia sino de no aplicar lo que ya se sabe; la checklist
  fuerza el ritual y deja evidencia. El checklist quirúrgico de la OMS redujo muertes ~47% en el
  piloto mundial.
- **Norman, forcing functions**: interlock (fuerza secuencia correcta), lock-in (impide salida
  prematura), lockout (impide entrar al estado peligroso). El diseño hace el mal uso imposible en
  vez de confiar en que el usuario recuerde.

Fuentes y URLs: reporte íntegro en el corpus interno del linaje (no publicado; ver la nota en
`decisiones/README.md`, secciones "manufacturing/safety lineage").
Estado de verificación de citas: `citas-verificadas.md`.
