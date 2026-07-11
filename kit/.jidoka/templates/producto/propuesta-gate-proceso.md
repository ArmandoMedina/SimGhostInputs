---
tipo: propuesta_gate_proceso
proceso: <nombre del proceso — p. ej. "cierre diario">
artefacto: <lo que se envía/publica/cierra — p. ej. "tabla diaria (Excel) → canal del equipo">
estado: en_definicion
---

# Propuesta — Gate de <proceso> (barrera de proceso)

> **Estado: PROPUESTA para decisión del dueño del riesgo.** Nada corre hasta que la columna
> "Dueño" esté marcada. Doctrina de gates: los disparos `deny-vs-ask`, `prueba-de-vida-del-gate`
> y `excepciones-cableadas` (`kit/.jidoka/disparos/`). Es una barrera de **proceso**: protege el
> artefacto del negocio (el envío/publicación), no el repo.

## 0. El choke point

- **Artefacto:** <qué se produce, con forma inspeccionable>
- **Choke point:** <el acto discreto de "esto se envía">
- **Riesgo si sale mal:** <qué cuesta y si es reversible — esto calibra todo lo demás>

## 1. Los checks

Regla de severidad: **deny** (bloqueo duro) para lo mecánico-verificable y lo irreversible;
**ask** (frena y el humano firma) para lo que requiere juicio. Fuente de cada check: el
instructivo/SOP real del proceso — cada paso manual es superficie de error y candidato a check.

| # | Check | Qué valida (y de qué paso del instructivo sale) | Propuesta | Dueño |
|---|---|---|---|---|
| 1 | <p. ej. fecha = hoy> | <qué error real evita> | deny | |
| 2 | <…> | <…> | ask | |

**Excepciones del negocio, cableadas con nombre** (no toleradas en silencio): <p. ej. "el
proveedor X puede amanecer negativo — esperado, no hallazgo">.

**Anti-fatiga:** pocos checks, tasa baja de falsas alarmas. Un ask que grita en falso seguido se
recalibra o se poda — un gate ruidoso entrena el reflejo de "click para pasar".

## 2. Checks históricos (ledger)

Los checks tipo "vs ayer" comparan contra un **ledger local** (JSONL, una línea por corrida; en
área no versionada si el dato es sensible). Sin historial se degradan a lo verificable hoy y lo
dicen. El registro al ledger se hace SOLO tras enviar de verdad.

## 3. Instrumentación del gate humano (fases posteriores)

- **Tablero de leading indicators:** tiempo de revisión, tasa de aprobación sin cambios,
  desacuerdos reportados, intercepciones reales. La prueba de vida: ¿cuándo fue la última vez
  que el gate rechazó algo real? Silencio total = gate podrido.
- **Capture-test (TIP):** trampas plantadas a baja frecuencia para medir que el revisor sigue
  despierto. Dos reglas no negociables: **fail-safe** (la trampa jamás llega al envío real) y
  **Just Culture** (el hit rate no castiga; si cae, se refresca entrenamiento). Se implementa
  tras ~1 mes de gate estable, fail-safe primero.
- **Práctica manual programada:** el proceso se corre a mano, en calma, con cadencia fija — y se
  compara contra la máquina. El diff enseña en ambas direcciones.

## 4. Antes de estrenar (obligatorio)

- [ ] **Prueba de humo contra el artefacto real.** Cazará bugs del propio gate y confirmará que
  bloquea lo que debe. Quien valida también se valida.
- [ ] Tests del gate con artefacto sintético del layout real (un test por check).

## Lo que el dueño del riesgo decide

- [ ] Columna "Dueño" de cada check (deny / ask / fuera).
- [ ] Frecuencia del TIP y regla Just Culture.
- [ ] Cadencia de la práctica manual.
- [ ] Orden de implementación.

<!-- tipo: propuesta_gate_proceso · proceso · artefacto · estado. Este es el molde mas
     "de proceso operativo": una segunda familia de barreras (protege el envio, no el repo).
     Borra este comentario al usar la plantilla. -->
