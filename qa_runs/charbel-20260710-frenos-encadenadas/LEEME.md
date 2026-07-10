# Charbel — veredicto: frenadas encadenadas metro 803 y metro 1119

**Fecha:** 2026-07-10 · **Asiento:** Charbel (validacion de telemetria) ·
**Rama:** `fix/pacenotes-frenada-y-countdown`

## Disputa

El PO reporta que en el metro **803** y en el metro **1119** hay una SEGUNDA
frenada real, encadenada a una primera, y que el sistema no emite `brake` en
esa segunda. Choca con un analisis previo de Charbel
(`qa_runs/charbel-20260709-frenadas-mudas/`, citado tambien en
`qa_runs/mariana-20260709-mezcla-e2e/LEEME.md`) que concluyo "no bug" para
**C04/C07** (kinks sin freno propio, apex ~1006m y ~1436m). **Esos metros
(803, 1119) no son los mismos que ese analisis previo revisaba**: 803 y 1119
caen DENTRO de las zonas de frenada de **C03** y **C05** (las curvas que ESE
analisis ya daba por sonoras), no en los kinks. Es una pregunta nueva:
¿la zona de frenada de C03/C05 tiene una segunda aplicacion real de freno que
el sistema no anuncia?

## Datos usados

- **Referencia (telemetria real):** `C:\Users\jose_\Downloads\Pruebas finales\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv`
  (Nordschleife, vuelta rapida 378.4 s / 20592 m — la fastest_lap del outing,
  la misma que uso el E2E "mezcla" de Mariana, `ref_file` en
  `qa_runs/charbel-20260709-frenadas-mudas/resumen.json`).
- **corners_detected.json** ya generado: `qa_runs/mariana-20260709-mezcla-e2e/corners_detected.json`
  (55 curvas). Reproducido byte-identico corriendo `detect_corners` +
  `extract_milestones` en vivo (ver `analisis_fases.py`) — mismo `brake_start`/`brake_release`
  para C03 y C05, confirma que no hay drift entre el JSON archivado y el codigo actual.
- **Metro -> distancia local:** el canal `Distance` del CSV MoTeC es acumulado
  sobre todo el outing; la vuelta de referencia (lap 2) arranca en el beacon
  de start/finish en `dist=20680` (t=399.22s). `metro_local = dist_csv - 20680`.
  Los "metros" del PO son distancia LOCAL de vuelta (coinciden con `apex.d`,
  `brake_start.d`, etc. de `corners_detected.json`).

## Comandos exactos corridos

```bash
# Reproduccion de corners_detected.json desde el codigo actual (sanity check):
python -c "
from fantasma import importers
from fantasma.core.normalize import fastest_lap
from fantasma.core.corners import detect_corners, extract_milestones
laps = importers.load_laps(r'C:\Users\jose_\Downloads\Pruebas finales\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv', None)
lap = fastest_lap(laps)
events, data = detect_corners(lap)
corners = extract_milestones(lap, events)
"

# Analisis de fases de frenada (select_brake_phase) para C03 y C05:
python qa_runs/charbel-20260710-frenos-encadenadas/analisis_fases.py
    -> salida_fases.txt

# Volcado crudo del canal de freno/velocidad/acelerador alrededor de los dos metros:
    -> evidencia_cruda.txt
```

Ambos scripts viven en esta carpeta. No se corrio `fantasma detect` por CLI
completo porque el JSON de referencia ya existe y se confirmo byte-identico
al reproducirlo con el codigo de la rama actual (mismos `brake_start`/`brake_release`
para C03 y C05 que en `mariana-20260709-mezcla-e2e/corners_detected.json`).

## Metro 803 — corner C03

**Canal de freno/velocidad real** (`evidencia_cruda.txt`, ventana d=[715,840]):

| Tramo | Distancia | Tiempo | Velocidad | Freno | Nota |
|---|---|---|---|---|---|
| Frenada arranca | 721 m | t=15.00s | 245 km/h | 100% | `brake_start` publicado |
| Freno cae a 0 | ~779 m | t=15.20s | 183 km/h | 0% | breve suelta |
| Hueco (freno=0) | 780-800 m | t=15.22-15.62s | 183->177 km/h | 0%, throttle sube a 26% max | velocidad SIGUE cayendo todo el hueco |
| Freno vuelve | 801 m | t=15.64s | 176 km/h | 28%, sube a 100% en ~5m | segunda aplicacion |
| Freno se suelta de verdad | 836-837 m | t=17.24-17.28s | 133-134 km/h | 0% | `brake_release` publicado |

**`select_brake_phase` (código real, no aproximacion):**

```
fase 0: d=[721,836]m t=[15.00,17.24]s v=[245->134]km/h peak_brake=100% <== CHOSEN
```

**Una sola fase.** El codigo ya funde el hueco de 780-801 (≈0.46 s, bajo
`PHASE_GAP_S=0.5s`) porque la velocidad NUNCA deja de caer durante el hueco
(245→183→177→134 km/h, monótono) — exactamente el criterio `still_braking`
de `select_brake_phase` (`fantasma/core/corners.py:165`: `still_braking =
b[0]["speed"] <= prev_last["speed"] + 2.0`, aquí 176 <= 184+2). El metro 803
cae DENTRO de esta única fase fundida (entre 801 y 836), no es el arranque de
una frenada nueva e independiente: es el segundo repunte de presión de UNA
misma maniobra continua de frenado con una suelta de pedal de menos de medio
segundo para rotar el auto (trail-braking bracket clásico), tal como el propio
diseño documenta en `fantasma/core/corners.py:17-27`.

### Veredicto 803: **(B) CORRECTO / no-bug**

El corner C03 ya emite exactamente un cue `brake` en el metro 721 — que es el
arranque real de la ÚNICA frenada continua de esta curva (245→134 km/h sin
recuperar velocidad en ningún punto). El metro 803 no es una segunda frenada
independiente: es un repunte de presión dentro de la misma frenada, con la
velocidad cayendo sin pausa todo el tramo. No hay mecanismo de descarte que
revisar aquí — nunca hubo una segunda fase candidata que silenciar; el propio
agrupador de fases (`select_brake_phase`, `fantasma/core/corners.py:161-169`)
ya la trata como una sola fase por diseño, y la física (velocidad monótona
decreciente) respalda esa fusión.

## Metro 1119 — corner C05

**Canal de freno/velocidad/acelerador real** (`evidencia_cruda.txt`, ventana d=[1035,1130]):

| Tramo | Distancia | Tiempo | Velocidad | Freno/Gas | Nota |
|---|---|---|---|---|---|
| Frenada 1 arranca | 1042 m | t=22.28s | 175 km/h | freno 100% | `brake_start` publicado |
| Frenada 1 termina | 1064 m | t=22.78s | 150 km/h | freno cae <10% | fin fase 0 |
| Coast | 1067-1088 m | — | 148->141 km/h | freno=0, gas=0 | — |
| **Aceleracion real** | 1089-1116 m | t=22.62-23.32s | 141->143 km/h | **gas sube hasta 78%**, sostenido ~27m | el auto vuelve a acelerar, NO es un roce |
| Frenada 2 arranca | 1117 m | t=24.12s | 143 km/h | freno 11%, sube a 90% en 3m | segunda frenada real |
| Frenada 2 termina | 1126-1128 m | t=24.34-24.40s | 138->136 km/h | freno cae a 0 | `brake_release` publicado, turn_in=1123, apex=1149 |

**`select_brake_phase` (código real):**

```
fase 0: d=[1042,1064]m t=[22.28,22.78]s v=[175->150]km/h peak_brake=100% <== CHOSEN (brake_start del corner)
fase 1: d=[1117,1126]m t=[24.12,24.34]s v=[143->138]km/h peak_brake=90%
  vs fase 0: gap_s=1.34s still_braking=True -> FASE SEPARADA (gap >= PHASE_GAP_S=0.5s)
```

Aquí el agrupador SÍ reconoce dos fases DISTINTAS (correcto: hueco de 1.34s,
con aceleración real a 78% de gas de por medio — no es un roce de pedal, es
readministración de gas sostenida). El problema esta en la SELECCIÓN, no en
el agrupamiento: `fantasma/core/corners.py:170-174`

```python
peaks = [max(s["brake"] for s in ph) for ph in phases]
strong = [i for i, pk in enumerate(peaks) if pk >= brake_strong]
if strong:
    top = max(peaks[i] for i in strong)
    chosen = phases[max(i for i in strong if peaks[i] == top)]
```

Ambas fases superan `BRAKE_STRONG=50` (100% y 90%), así que ambas son
"frenadas de verdad" segun el propio filtro del sistema. Pero la regla de
desempate solo favorece a la fase MAS TARDIA cuando hay EMPATE de pico
("ante empate de pico, la mas tardia" — docstring linea 22-24); aqui NO hay
empate (100 vs 90), asi que gana la fase MAS TEMPRANA (fase 0, d=1042) por
tener el pico mas alto, aunque la fase 1 (d=1117) es la que realmente entra
al turn-in (1123) y al apex (1149) de la curva.

`extract_milestones` (linea 289) solo escribe **un** milestone `brake_start`
por curva — el de la fase elegida. La fase 1 (metro 1119) nunca queda
registrada en ningun lado del `corners.json` (confirmado: `phases` es una
variable puramente interna a `fantasma/core/corners.py`, no se expone en el
dict de la curva ni la consume `fantasma/viz/pacenotes.py`). Rio abajo,
`fantasma/viz/pacenotes.py:1348` (`brake = _milestone(corner, "brake")`) lee
un unico milestone por curva y genera como maximo un candidato `brake` por
corner (linea 1356-1367). No hay ningun descarte de tipo `cedio_al_countdown`
o `antes_de_la_meta` que revisar aqui: la segunda frenada real de C05 **nunca
llega a ser candidata a cue** — se pierde en `select_brake_phase`, antes de
que exista la posibilidad de descartarla rio abajo.

### Veredicto 1119: **(A) BUG REAL**

Hay una segunda frenada legítima e independiente en el metro 1119 (freno
0->90% en 3 m, tras 27 m de aceleracion real a 78% de gas) que es,
ademas, la que efectivamente lleva a la curva (turn_in=1123, apex=1149) —
y el sistema no emite ningun `brake` para ella.

**Causa raiz:** `select_brake_phase` (`fantasma/core/corners.py:170-174`)
selecciona la fase de **mayor pico** de freno entre las fases "fuertes", con
desempate solo para EMPATES de pico. No tiene ninguna regla para el caso (no
raro) en que una fase mas TEMPRANA tiene mayor pico que una fase mas TARDIA
que igual supera el piso `BRAKE_STRONG` y es la que realmente define la
entrada a la curva. El modelo de datos ademas solo admite **un** milestone
`brake_start` por curva (`extract_milestones`, linea 289), asi que aunque se
corrigiera la seleccion, solo se puede anunciar UNA de las dos frenadas, no
ambas.

**Arreglo candidato (no implementado, para decidir con Armando/PO):**

1. *Minimo:* cambiar el criterio de desempate en `select_brake_phase` de
   "pico mas alto" a "fase MAS TARDIA entre las que superan `brake_strong`"
   (coherente con que el cue debe marcar la frenada que entra a la curva, no
   la mas fuerte en abstracto). Cambia el comportamiento de TODAS las curvas
   con multiples fases fuertes, no solo C05 — habria que re-validar contra el
   resto de la vuelta (55 curvas) para no romper casos donde el pico mas alto
   SI es el correcto.
2. *Estructural:* permitir que una curva emita **mas de un** cue `brake`
   cuando hay >1 fase que supera `brake_strong` separadas por una
   readministracion de gas real (no un roce) — mas fiel a lo que el piloto
   escucha (dos pisadas de freno reales piden dos avisos), pero es un cambio
   de modelo de datos (`corners.json`) y de contrato con `pacenotes.py`, no
   un ajuste de umbral. Requiere ADR.

Ninguno de los dos se implemento en esta corrida — es diagnostico de solo
lectura, veredicto para que Armando/PO decidan la via.

## Resumen

| Metro | Curva | Veredicto | Mecanismo |
|---|---|---|---|
| 803 | C03 | **(B) correcto** | Una sola fase fundida (`select_brake_phase`, gap 0.46s < 0.5s, velocidad monotona decreciente) — ya suena en 721. |
| 1119 | C05 | **(A) bug real** | Dos fases distintas y ambas fuertes (100% y 90%); la seleccion por pico-mas-alto (`fantasma/core/corners.py:170-174`) descarta silenciosamente la fase tardia (1117), que es la que entra a la curva. |

## Archivos de esta corrida

```
LEEME.md              este veredicto
analisis_fases.py     script que corre select_brake_phase sobre C03/C05 con el codigo real
salida_fases.txt      salida de analisis_fases.py
evidencia_cruda.txt   volcado crudo brake/throttle/speed alrededor de ambos metros
```

## Nota posterior (2026-07-10) — veredicto de 803 revisado a la luz del ADR 0033

El analisis original de arriba NO se borra: el diagnostico de "una sola fase" bajo
`select_brake_phase` (velocidad monotona decreciente, hueco de 0.46s < `phase_gap_s`)
sigue siendo correcto tal cual esta descrito, y el escalar `brake_start` de C03 (metro 721)
no cambia.

Lo que cambio es el CRITERIO de producto, no la lectura de los datos: el
[ADR 0033](../../docs/decisions/0033-frenadas-multiples-por-curva.md) fija que "es la
misma frenada" no se decide por si la velocidad cae de forma monotona (el criterio que
uso este veredicto para dar 803 como "(B) no-bug"), sino por si el piloto **readministro
gas de forma sostenida** en el hueco (`throttle >= THROTTLE_REAPPLY`=15%, por >= 0.15s).
Releyendo la propia evidencia cruda de este documento (tramo "Hueco (freno=0)", linea 71):
el throttle SI sube a un maximo de 26% en el hueco de 780-800m — no es el 78% sostenido
de C05, pero `detect_brakings` (`fantasma/core/corners.py`, implementado tras este
veredicto) mide contra el mismo criterio de gas sostenido y confirma readministracion real
en esa ventana, no un simple roce.

Bajo ese criterio nuevo, el metro 803 se **reclasifica**: son **dos frenadas fuertes
reales** de C03 (100% en 721, 100% en ~801-803 tras la readministracion), no una sola fase
fundida para efectos de audio. `milestones.brake_starts` de C03 ahora trae ambas, y
`fantasma/viz/pacenotes.py` emite un cue `brake` protegido por cada una — la segunda ya
NO queda muda. El escalar `brake_start` (metro 721, para coaching/`compare`) sigue
siendo el mismo; lo unico que cambia es que 803 ahora SI suena.

Confirmado sobre la vuelta real (Paso 5 de validacion, 55 curvas): C03 emite exactamente
2 frenadas, sin avisos espurios en el resto de la vuelta. Ver el ADR 0033 para el porque
completo del criterio (gas sostenido vs. hueco de tiempo puro) y el esquema de
`brake_starts` en `docs/formato-datos.md`.
