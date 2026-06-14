# Brief de Producto — SimGhostInputs

> Este documento es el norte del proyecto. Define qué es, para quién es, hasta dónde llega y por qué se tomaron las decisiones que se tomaron. Antes de añadir una función nueva, este es el primer lugar donde buscar si tiene cabida aquí.

---

## 1. El Problema

MoTeC i2 es una herramienta poderosa. También tiene una curva de aprendizaje que no está justificada para alguien que corre por hobby y quiere mejorar sus tiempos sin convertir el sim racing en un segundo trabajo.

El problema no es la telemetría —los datos existen y son ricos— sino el costo de extraer valor de ellos: horas aprendiendo software profesional de análisis para responder preguntas simples como *¿dónde estoy perdiendo tiempo?* o *¿qué hace diferente la vuelta de referencia en esa curva?*

Ese es el problema que SimGhostInputs resuelve.

---

## 2. Nicho

**Para quién es:**
- Sim racers que corren por hobby o de forma semi-competitiva
- Pilotos que quieren mejorar sus tiempos con datos reales, sin invertir horas en software de telemetría profesional
- Quienes ya tienen una vuelta de referencia (propia o de un coach) y quieren entender qué diferencia hay con la suya, curva por curva

**Para quién NO es:**
- Equipos profesionales con ingenieros de datos dedicados (para eso existe MoTeC i2, i2 Pro y Atlas)
- Pilotos que buscan telemetría en tiempo real dentro del sim (para eso existe CrewChief, que ya lo resuelve bien)
- Usuarios que quieren que el software tome las decisiones por ellos mediante IA

---

## 3. El Insight Clave

El 80% de la mejora en un circuito viene de resolver el 20% de las curvas donde se pierde más tiempo. Identificar ese 20% no requiere inteligencia artificial, no requiere nube y no requiere suscripción mensual.

Requiere comparar dos vueltas metro a metro y mostrar la diferencia de forma clara.

**Este proyecto explora hasta dónde se puede llegar con análisis dinámico usando solo aritmética sobre datos.** Sin modelos de lenguaje en el pipeline de comparación. Sin latencia de red. Sin costos por uso. La precisión no viene de algoritmos sofisticados — viene de hacer las preguntas correctas sobre los datos que ya existen.

---

## 4. Los Dos Productos de Este Repositorio

### Producto 1 — Análisis Post-Tanda

**Qué resuelve:** después de una sesión, el piloto quiere saber dónde perdió tiempo y qué hizo diferente.

**Cómo funciona:** importa el CSV exportado desde MoTeC i2 (o CSV genérico), compara la vuelta del piloto contra una vuelta de referencia metro a metro, y genera un reporte accionable en minutos.

**Qué entrega:**
- Reporte narrativo en Markdown: dónde pierdes, cuánto y en qué fase de cada curva
- Gráficas ghost: velocidad / gas / freno / volante del piloto superpuesto sobre la referencia, curva por curva
- Diagrama G-G: si estás usando el agarre disponible
- Mapa de delta: el tiempo ganado o perdido a lo largo de toda la vuelta
- Tabla de curvas con tiempo perdido ordenado de mayor a menor impacto

**El objetivo:** llegar del CSV al insight accionable en menos de cinco minutos.

---

### Producto 2 — Overlay de Video

**Qué resuelve:** los datos solos no siempre son suficientes. Ver exactamente qué hiciste en la frenada de Hatzenbach mientras ves el video de esa frenada cambia la comprensión por completo.

**Cómo funciona:** genera un HUD animado con canal alfa (transparente) sincronizado con la telemetría del piloto y lo superpone sobre la grabación del sim. El HUD incluye los inputs del piloto y los de la referencia en simultáneo, para que la comparación sea visual e inmediata.

**Qué entrega:**
- Overlay `.webm` con canal alfa: el HUD listo para pegar en cualquier editor de video
- Composición automática con ffmpeg: el video final con el HUD integrado en un solo paso
- Auto-sincronización: detecta automáticamente el offset entre el video y la telemetría por correlación de audio, sin que el piloto tenga que contar segundos a mano

**El objetivo:** ver lo que hiciste mal en el contexto visual real de la vuelta, con la referencia al lado.

---

### Cómo se complementan

```
Sesión en pista
      │
      ▼
CSV exportado de MoTeC i2
      │
      ├──▶ [Producto 1] Análisis post-tanda
      │         Reporte · Gráficas · Tabla de curvas
      │
      └──▶ [Producto 2] Overlay de video
                HUD animado · Video compuesto · Auto-sync
```

Ambos productos comparten el mismo motor de importación, normalización y comparación. Son dos formas distintas de consumir el mismo análisis.

---

## 5. Alcance

### Está dentro de este repositorio

| Función | Descripción |
| :-- | :-- |
| Importadores de telemetría | MoTeC CSV/XLSX, CSV genérico con mapeo |
| Normalización por distancia | Metro 0 en meta, remuestreo configurable |
| Detector de curvas e hitos | V-Min, G-lat, frenada, ápex, gas |
| Comparador piloto vs referencia | Delta continuo, Δ V-Min, Δ frenada, tiempo perdido |
| Reportes exportables | `report.md`, `delta.csv`, `corners_compare.csv` |
| Gráficas de análisis | Delta map, G-G, full lap, curvas, zonas de frenada |
| Overlay HUD animado | VP9/ProRes con canal alfa, render paralelo |
| Composición de video | ffmpeg con NVENC automático si hay GPU NVIDIA |
| Auto-sincronización | Detección de offset por correlación audio/telemetría |
| Interfaz gráfica local | Streamlit en localhost, sin hosting, datos siempre locales |
| Nuevos importadores | iRacing `.ibt`, `.ld` directo, SimHub CSV, otros formatos |
| Historial entre sesiones | Comparación de tendencias entre tandas (Fase 2.4, pendiente) |

### Está fuera de este repositorio

| Fuera de scope | Por qué |
| :-- | :-- |
| Coach de voz en tiempo real | Es un producto separado con stack, dependencias y restricciones completamente distintas → `fantasma-live` |
| Listener de telemetría UDP en vivo | Requiere correr mientras AMS2 usa la GPU al límite — incompatible con las restricciones de hardware de este pipeline |
| Vueltas de referencia incluidas | Cada usuario trae sus propios datos. Este repo es el motor, no el contenido |
| API REST o servicio en nube | Los datos del piloto no deben salir de su máquina |
| IA o LLM en el pipeline de comparación | El comparador es aritmética pura; un modelo de lenguaje solo añade latencia y costo sin mejorar la precisión |
| Duplicar CrewChief | El spotter, combustible y daños ya están resueltos por CrewChief. No reinventar |

---

## 6. Horizonte de Este Repositorio

**Lo que falta por construir aquí:**

| Fase | Objetivo |
| :-- | :-- |
| 2.4 — Histórico entre sesiones | Comparar el rendimiento en una curva a lo largo de varias tandas. Ver si se progresa o se retrocede |

Eso completa el scope de `fantasma-inputs`. Una vez ahí, el motor offline es funcional para el 80/20 que motivó el proyecto.

**Lo que viene después, en otro repositorio:**

`fantasma-live` — coach de voz en tiempo real: escucha la telemetría UDP de AMS2 mientras el piloto conduce y habla en el casco usando el análisis de vueltas anteriores como referencia. Stack completamente distinto: listener UDP, síntesis de voz (TTS), latencia <200 ms, sin matplotlib ni ffmpeg.

El motivo de la separación es simple: mientras AMS2 corre, la GPU está al límite con VR. Todo lo que corra en ese momento tiene restricciones radicalmente distintas a un pipeline de análisis post-tanda.

---

## 7. Principios de Diseño

Estas decisiones no se negocian. Son el por qué detrás de cómo está construido el proyecto.

**CLI primero.** La interfaz gráfica es una capa opcional sobre el CLI. Todo lo que hace la UI se puede hacer desde la terminal. Sin lock-in, scriptable, automatizable.

**Datos locales, siempre.** La telemetría del piloto no sale de su máquina. Sin cuentas, sin tokens, sin APIs de terceros en el pipeline de comparación.

**Salidas estándar.** CSV, Markdown, PNG, WebM. Nada propietario. Si mañana SimGhostInputs desaparece, los archivos de salida siguen siendo legibles.

**Sin GPU durante la sesión.** El pipeline de análisis y render corre en CPU. La GPU es exclusiva de AMS2 + VR mientras se conduce. Solo `fantasma compose` usa NVENC, y solo post-sesión.

**Dependencias opcionales, siempre opcionales.** El núcleo (`core/`) funciona sin matplotlib, sin scipy, sin openpyxl. Cada función avanzada se instala solo si se necesita.

**AGPL-3.0.** Si una herramienta ayuda a la comunidad a mejorar, las mejoras de esa herramienta también deben volver a la comunidad.

---

## 8. Cómo Se Ve el Éxito

No hay métricas de negocio porque no hay negocio. Hay preguntas concretas de uso:

- ¿Puedes llegar del CSV exportado de MoTeC al reporte accionable en menos de cinco minutos?
- ¿El reporte te dice con claridad en qué curva perder más tiempo es tu mayor palanca de mejora?
- ¿El overlay de video te muestra la diferencia entre tu frenada y la de la referencia sin que tengas que buscarla?
- ¿Puedes correr en pista, volver, analizar y tener el video con el HUD listo antes de que se enfríe el entusiasmo de la sesión?

Si la respuesta a esas cuatro preguntas es sí, el producto funciona.

---

*SimGhostInputs es un proyecto de hobby construido por un sim racer para sim racers. El código es libre, los datos son tuyos y el objetivo es simple: mejorar más rápido en menos tiempo.*
