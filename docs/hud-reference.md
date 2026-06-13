# Referencia del HUD (overlay)

El overlay HUD-A es un video con canal alfa (fondo transparente) de la duración exacta
de la vuelta del piloto. Se pega como pista superior sobre la grabación del sim para
obtener el video de análisis.

---

## Anatomía del HUD

```
┌──────────────────────────────────────────────────────────────────────┐
│  GAP: +0.412s  │  ΔV: -8 km/h  │  SLIP: 1.23  │  ABS: 2  │ M: 3 │ 187 │ 3412m │
│                                                                      │
│  PANEL GAS          PANEL FRENO          PANEL VOLANTE              │
│  ─────────────      ─────────────         ─────────────             │
│  ▲ 100%             ▲ 100%                ▲ derecha                  │
│  │  ╔══╗            │   ╔╗                │     ╔═╗                  │
│  │  ║  ║  piloto    │   ║║  piloto        │     ║ ║ piloto          │
│  │──╫──╫──────────  │───╫╫───────────────│─────╫─╫──── cursor      │
│  │  ╚══╝            │   ╚╝                │     ╚═╝ referencia      │
│  ▼ 0%              ▼ 0%                  ▼izquierda                  │
│                   ◄──────────────────────────►                       │
│                  -320m    CURSOR    +200m                            │
└──────────────────────────────────────────────────────────────────────┘
```

### Franja de datos (parte superior)

| Campo | Qué muestra | Cuándo es útil |
| :-- | :-- | :-- |
| **GAP** | Diferencia de tiempo acumulada respecto a la referencia en el metro actual. Positivo (rojo) = el piloto va más lento; negativo (verde) = más rápido. | Ver si estás ganando o perdiendo tiempo en cada sección. |
| **ΔV** | Diferencia de velocidad puntual (piloto − referencia) en el metro exacto donde está el cursor. Negativo = más lento. | Identificar dónde no estás llegando a la velocidad de la referencia. |
| **SLIP** | Índice de deslizamiento de las ruedas (velocidad de rueda vs velocidad real). Proxy de desgaste y carga lateral. | Monitorear si estás más agresivo con el neumático que la referencia. |
| **ABS** | Activaciones del ABS en el segmento de 320m anterior al cursor. | Ver si estás bloqueando ruedas en más frenadas que la referencia. |
| **M** / **MARCHA** | Marcha actual del piloto (1–6 / N / R). | Verificar sincronía visual: comparar con el marcador de marcha del sim. |
| **km/h** | Velocidad instantánea del piloto. | Verificar sincronía y detectar diferencias de velocidad punta en rectas. |
| **metros** | Distancia recorrida en la vuelta desde meta. | Referencia espacial; úsalo con el vídeo para confirmar en qué metro estás. |

---

## Los tres paneles

Cada panel muestra **una ventana deslizante de 520 m** centrada en el cursor (320 m hacia atrás,
200 m hacia adelante). Eje horizontal = distancia de vuelta en metros; eje vertical = intensidad del canal.

El **cursor** (línea amarilla vertical) es el instante actual. Lo que está a la izquierda ya pasó;
lo que está a la derecha es lo que viene.

Cada panel tiene **dos líneas**: el **piloto** (brillante) y la **referencia** (apagada/gris).
La diferencia visual entre ambas líneas es la historia del delta: si la línea del piloto va por encima
de la referencia en freno, el piloto está frenando más fuerte; si el gas del piloto sube más tarde,
está tardando más en abrir.

---

## Código de colores

### Panel de gas (acelerador)

| Color | Quién | Qué significa |
| :-- | :-- | :-- |
| **Verde vívido** `#00c853` | Piloto | Aceleración normal |
| **Violeta vívido** `#e040fb` | Piloto | TCS activo (el sim está limitando el gas por deslizamiento) |
| **Gris** `#9aa0a6` | Referencia | Gas normal de la referencia |
| **Violeta apagado** `#7b5ea7` | Referencia | TCS activo en la referencia |

### Panel de freno

| Color | Quién | Qué significa |
| :-- | :-- | :-- |
| **Rojo vívido** `#ff1744` | Piloto | Frenada normal |
| **Ámbar vívido** `#ffab00` | Piloto | ABS activo (ruedas bloqueando) |
| **Gris** `#9aa0a6` | Referencia | Freno normal de la referencia |
| **Ámbar apagado** `#b8860b` | Referencia | ABS activo en la referencia |

### Panel de volante (steering)

| Color | Quién | Qué significa |
| :-- | :-- | :-- |
| **Azul claro** `#40c4ff` | Piloto | Giro dentro de la carga lateral normal (< P75 de la referencia) |
| **Amarillo** `#fdd835` | Piloto | Carga lateral media — entre P75 y P90 del G-lat de la referencia |
| **Naranja** `#ff6d00` | Piloto | Carga lateral alta — por encima del P90 del G-lat de la referencia |
| **Gris** `#9aa0a6` | Referencia | Ángulo normal de la referencia |
| **Amarillo apagado** `#6b5e00` | Referencia | Zona de carga lateral media (referencia) |
| **Naranja apagado** `#7a3300` | Referencia | Zona de carga lateral alta (referencia) |

> **¿Por qué los umbrales del volante son relativos a la referencia?**
> Los percentiles P75 y P90 del `|G-lat|` se calculan sobre la vuelta de referencia. Así «amarillo»
> significa «trabajando al mismo nivel que la referencia» y «naranja» significa «más allá de donde
> normalmente trabaja la referencia en esa zona». No necesitas calibrar nada manualmente.

---

## Cómo leer el HUD en la práctica

### ¿Dónde estoy perdiendo tiempo?

1. Mira el **GAP**: si sube (se pone más rojo/positivo) en una frenada, estás perdiendo tiempo ahí.
2. Compara las líneas de freno: si la tuya (roja) aparece ANTES que la de la referencia (gris), frenas antes. Si aparece DESPUÉS, frenas más tarde.
3. Compara las líneas de gas: si la referencia (gris) sube antes que la tuya (verde) en la salida de una curva, la referencia abre gas antes.

### Señales de alerta comunes

| Lo que ves | Qué significa |
| :-- | :-- |
| Línea de piloto en violeta frecuente | TCS corrigiendo mucho — posible exceso de gas en salidas |
| Línea de piloto en ámbar frecuente | ABS disparándose — posible punto de frenada demasiado agresivo |
| Volante naranja donde la referencia es azul | Piloto generando más G-lat — línea diferente o mayor velocidad de paso |
| GAP aumentando en zona de gas | El piloto está tardando más en retomar velocidad después de la curva |
| GAP estable en rectas pero aumentando en curvas | El problema es el ápex, no la potencia |

### Verificar la sincronía

Los campos **MARCHA**, **km/h** y **metros** en la franja superior permiten confirmar que
el overlay y el video de grabación están alineados:

- Pausa el video en un momento reconocible (p. ej. entrada a una curva lenta).
- Compara la marcha que muestra el HUD con la que muestra el sim en el video.
- Si no coinciden, ajusta el offset con `fantasma compose --offset` o `--auto-sync`.

---

## Opciones de renderizado

```
# Formato recomendado: WebM VP9 con alpha (compatible con cualquier editor)
fantasma overlay --reference ref.csv --driver mi.csv -o salida/ --format webm

# Máxima calidad: ProRes 4444 (para DaVinci Resolve / Final Cut)
fantasma overlay --reference ref.csv --driver mi.csv -o salida/ --format prores

# Solo el tramo de las 3 curvas problemáticas (más rápido para iteración)
fantasma overlay --reference ref.csv --driver mi.csv -o salida/ --start 120 --end 180

# Render en lote de todas las vueltas completas de la sesión
fantasma overlay --reference ref.csv --driver mi.csv -o salida/ --all-laps
```
