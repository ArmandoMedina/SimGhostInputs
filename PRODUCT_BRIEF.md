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

## 4. Landscape — Qué Existe y Qué No

Se hizo una revisión exhaustiva del ecosistema open source en junio 2026. Estos son los proyectos más relevantes encontrados y por qué ninguno cubre el mismo territorio:

| Proyecto | Licencia | Qué hace | Por qué no es lo mismo |
| :-- | :-- | :-- | :-- |
| [TrackDataAnalysis](https://github.com/racer-coder/TrackDataAnalysis) | MIT | GUI de escritorio, comparación por distancia, reproduce video en sinc con datos | No genera overlay WebM, no importa CSV de MoTeC i2, no auto-sync por audio |
| [simracing-ai-coach](https://github.com/POWERRRRRRRR/simracing-ai-coach) | MIT | Comparación por distancia en AC, reporte HTML, coaching por LLM | Solo Assetto Corsa, reporte HTML (no Markdown), sin video |
| [LMU-Telemetry-Lab](https://github.com/rabbit20031225/LMU-Telemetry-Lab) | MIT | Ghost car 3D + comparación por distancia en LMU | Solo LMU, HUD en vivo (no exportable), sin CSV MoTeC |
| [TinyPedal](https://github.com/TinyPedal/TinyPedal) | GPL-3.0 | Overlay de telemetría en tiempo real para rF2/LMU | Sin análisis post-sesión, sin video exportado |
| [b4mad/racing](https://github.com/b4mad/racing) | GPL-3.0 | Telemetría comunitaria vía MQTT → Grafana | Cloud, en vivo, sin análisis post-sesión, sin video |
| [PurpleSector](https://github.com/chrismarth/PurpleSector) | AGPL-3.0 | Coaching post-sesión con IA para AC | Solo Assetto Corsa, sin video, sin MoTeC CSV |

**Conclusión:** Ningún proyecto open source encontrado combina el pipeline completo de SimGhostInputs: importar CSV de MoTeC i2 → reporte Markdown con gráficas → overlay WebM renderizado con canal alfa → auto-sincronización por correlación de audio con video grabado. Los proyectos existentes cubren partes del problema (comparación por distancia, overlay en vivo, reporte post-sesión) pero con enfoques, stacks y flujos de trabajo completamente distintos.

### Nota sobre CrewChief

[CrewChief](https://github.com/mrbelowski/CrewChiefV4) es la herramienta de referencia para coaching de voz en tiempo real en simracing. Su código es público en GitHub pero no tiene archivo de licencia formal — legalmente es "All Rights Reserved" por defecto. No se recomienda forkear ni incorporar su código.

Lo relevante para este proyecto: CrewChief expone un canal **MQTT** documentado que publica telemetría en tiempo real. Si en el futuro `fantasma-live` necesita capturar datos durante la sesión, MQTT es el mecanismo de integración limpio — sin forkear CrewChief, sin dependencia de su licencia ambigua.

---

## 5. Los Dos Productos de Este Repositorio

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

## 6. Alcance

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
| Interfaz gráfica local | NiceGUI + pywebview, ventana de escritorio nativa, sin hosting, datos siempre locales; disponible como instalador doble-clic (Windows) |
| Nuevos importadores | iRacing `.ibt`, `.ld` directo, SimHub CSV, otros formatos |
| Historial entre sesiones | Comparación de tendencias entre tandas (diferido a post-v1.0) |

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

## 7. Horizonte de Este Repositorio

**Lo que falta por construir aquí:**

| Pendiente (post-v1.0) | Objetivo |
| :-- | :-- |
| Histórico entre sesiones | Comparar el rendimiento en una curva a lo largo de varias tandas. Ver si se progresa o se retrocede |

Eso completa el scope de `fantasma-inputs`. Una vez ahí, el motor offline es funcional para el 80/20 que motivó el proyecto.

**Lo que viene después, en otro repositorio:**

`fantasma-live` — coach de voz en tiempo real: escucha la telemetría UDP de AMS2 mientras el piloto conduce y habla en el casco usando el análisis de vueltas anteriores como referencia. Stack completamente distinto: listener UDP, síntesis de voz (TTS), latencia <200 ms, sin matplotlib ni ffmpeg.

El motivo de la separación es simple: mientras AMS2 corre, la GPU está al límite con VR. Todo lo que corra en ese momento tiene restricciones radicalmente distintas a un pipeline de análisis post-tanda.

---

## 8. Principios de Diseño

Estas decisiones no se negocian. Son el por qué detrás de cómo está construido el proyecto.

**CLI primero.** La interfaz gráfica es una capa opcional sobre el CLI. Todo lo que hace la UI se puede hacer desde la terminal. Sin lock-in, scriptable, automatizable.

**Datos locales, siempre.** La telemetría del piloto no sale de su máquina. Sin cuentas, sin tokens, sin APIs de terceros en el pipeline de comparación.

**Salidas estándar.** CSV, Markdown, PNG, WebM. Nada propietario. Si mañana SimGhostInputs desaparece, los archivos de salida siguen siendo legibles.

**Sin GPU durante la sesión.** El pipeline de análisis y render corre en CPU. La GPU es exclusiva de AMS2 + VR mientras se conduce. Solo `fantasma compose` usa NVENC, y solo post-sesión.

**Dependencias opcionales, siempre opcionales.** El núcleo (`core/`) funciona sin matplotlib, sin scipy, sin openpyxl. Cada función avanzada se instala solo si se necesita.

**AGPL-3.0.** Si una herramienta ayuda a la comunidad a mejorar, las mejoras de esa herramienta también deben volver a la comunidad.

---

## 9. Cómo Se Ve el Éxito

No hay métricas de negocio porque no hay negocio. Hay preguntas concretas de uso:

- ¿Puedes llegar del CSV exportado de MoTeC al reporte accionable en menos de cinco minutos?
- ¿El reporte te dice con claridad en qué curva perder más tiempo es tu mayor palanca de mejora?
- ¿El overlay de video te muestra la diferencia entre tu frenada y la de la referencia sin que tengas que buscarla?
- ¿Puedes correr en pista, volver, analizar y tener el video con el HUD listo antes de que se enfríe el entusiasmo de la sesión?

Si la respuesta a esas cuatro preguntas es sí, el producto funciona.

---

*SimGhostInputs es un proyecto de hobby construido por un sim racer para sim racers. El código es libre, los datos son tuyos y el objetivo es simple: mejorar más rápido en menos tiempo.*

---

## 10. Concepto de UX — Drill-down por curva

> Capturado 2026-06-14. Primera versión implementada el 2026-06-30 como panel de Paso 2 basado en `corner_coaching(row, trace)`. Puede crecer después con más señales, pero mantiene la regla de aritmética pura.

La tabla actual de curvas muestra tiempo perdido ordenado de mayor a menor. El siguiente paso natural es hacerla interactiva: el piloto selecciona una curva y ve exactamente qué corregir.

**Flujo:**
1. Vista principal: lista de curvas ordenadas por tiempo perdido (mayor → menor)
2. Click en una curva → panel de detalle con coaching específico calculado desde los datos

**Qué mostraría el detalle:**
- **Punto de frenada:** cuántos metros antes/después de la referencia (`Δ frenada`)
- **Intensidad de frenada:** si el piloto frena más suave o más fuerte que la referencia (curva de presión)
- **Progresividad:** qué tan lineal/abrupto es el perfil de freno comparado con la referencia
- **V-Min (ápex):** velocidad de paso target, cuánto más/menos lleva el piloto
- **Gas:** cuántos metros después de la referencia abre el gas, qué tan progresivo
- **Volante / G-lat:** si el piloto genera más o menos carga lateral, en qué fase de la curva
- **Marchas / RPM:** si usa la misma marcha o una diferente (impacto en tracción en la salida)
- **Síntesis en lenguaje natural:** "Frenas 40 m antes con 15% menos intensidad → llegas 8 km/h más lento al ápex → pierdes 0.6 s en la salida" — derivado de aritmética, no de LLM

**Por qué encaja en el proyecto:**
El insight 80/20 dice que pocas curvas concentran la mayoría del tiempo perdido. La tabla ya las ordena. El drill-down convierte el dato en instrucción concreta sin salir de los principios: aritmética pura, sin red, sin IA.
