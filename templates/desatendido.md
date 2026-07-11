# Corrida desatendida — <fecha> · <alcance>

> Trabajo autónomo, sin humano presente. Doctrina: `kanban/desatendido.md`. Rama: `auto/<fecha>`. **Archivo temporal:** se retira cuando ambas lanes quedan vacías; lo durable ya migró a ADR / HANDOFF / CHANGELOG.
> Prioridad declarada: **seguridad y fugas > corrección > robustez > salud de docs > estilo**.

## Reconocimiento (qué revisé y está sano)

- <Lo que se inventarió y quedó **sano** — confirma que hubo cobertura real, no solo hallazgos.>

## Lane [agente] — ejecutado solo (mecánico, reversible, autorizado)

En orden de prioridad. Secciones vacías a propósito si no hay nada.

### A. Seguridad y fugas
- [ ] `A1` — <acción> · verificación: <criterio> · *(hecho AAAA-MM-DD: <evidencia>)*

### B. Corrección
- [ ] `B1` — <acción> · verificación: <criterio>

### C. Robustez
- (vacío)

### D. Salud de docs y método
- [ ] `D1` — <acción> · verificación: <criterio>

### E. Estilo
- (vacío)

## Lane [humano] — click-it-down (juicio / irreversible / credenciales)

Lo que la corrida **NO** decidió sola. Cada ítem nombra qué firma el humano y qué puede hacer una corrida después.

- **§1 <tema>** — **[humano]** <la decisión irreversible o de juicio que solo tú tomas>; **[agente]** <lo que queda listo para ejecutar una vez decidido>.
- **§2 <cambio a un gate>** — **[humano]** revisa y aprueba el borrador (el agente NO edita sus propios gates); **[agente]** dejó el borrador en <ruta>.

## Descartado a propósito

- <Lo que NO se hizo y por qué — evita inflar el backlog y deja el juicio registrado.>
