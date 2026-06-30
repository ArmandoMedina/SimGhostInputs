# Patrones de UX/UI y gate de calidad de interfaz

> **Para qué es este documento.** Así como el repo tiene convenciones de **código** (ruff, tests)
> y de **docs** (§8 de `CONTRIBUTING.md`), este es el estándar de **interfaz**: las heurísticas que
> la UI (`fantasma ui`, Streamlit) y el HUD deben cumplir, y **el gate que verifica que se cumplan
> antes de subir cambios** — análogo a "los tests deben pasar". Lo usa el rol **Mariana** (UX) como
> rúbrica, y se integra con las barreras de [`flujo-de-trabajo.md`](flujo-de-trabajo.md).
>
> **Principio rector (igual que en todo el repo): determinismo bloquea, juicio aconseja.** La
> calidad de UX tiene una parte **medible** (regresión de layout, contraste, elementos presentes,
> estados de carga) que **puede bloquear como un test**; y una parte **subjetiva** ("¿se ve
> profesional?, ¿el flujo se siente claro?") que **no** puede ser portero automático — es el
> checkpoint humano de Mariana que vuelve al PO. Forzar lo subjetivo como gate produce falsos
> rojos y se ignora; no medir lo objetivo deja pasar regresiones. El gate respeta esa frontera.

---

## 1. Heurísticas (la rúbrica)

Adaptación de las heurísticas de Nielsen al dominio (sim racing, análisis post-tanda, local-first).
Cada cambio de UI/HUD se evalúa contra esto.

1. **Visibilidad del estado del sistema.** El usuario siempre sabe qué pasa: progreso de render con
   %, qué encoder se usó (NVENC vs CPU) y cuánto tardó, qué vuelta/flujo está activo, qué paso sigue.
   *Hoy falla en:* no se reporta el encoder ni el tiempo de compose (C20).
2. **Lenguaje del usuario, no del sistema.** Vocabulario de pista: "frenada", "ápex", "tiempo
   perdido", "vuelta de referencia" — no "buffer", "tempfile", "exit code". *Regresión histórica:*
   mostrar la ruta de un tempfile en vez del nombre del archivo (ya corregido).
3. **Prevención de errores > mensajes de error.** Chequear prerrequisitos **antes** de dejar entrar
   a un flujo: ffmpeg presente para video (C19), columnas mapeables para CSV no-MoTeC (C07),
   referencia vs piloto distintos. Mejor desactivar/avisar que dejar fallar a mitad.
4. **Reconocer en vez de recordar.** El usuario no memoriza flags: el wizard de 5 pasos y los flujos
   predefinidos exponen las opciones. *Deuda:* capacidades del CLI no expuestas en UI (mapeo de
   columnas, comparar dos vueltas del mismo archivo, editar nombres de curva — C07/C10/C13).
5. **Disclosure progresivo.** Lo avanzado se esconde tras expanders; lo esencial primero. El Paso 0
   ya usa expander para la guía de export. *Riesgo:* pantallas demasiado densas de texto.
6. **Control y libertad del usuario.** Cancelar un render largo, volver a procesar otra vuelta sin
   recargar, navegar sin perder estado. *Ya cubierto* (Detener render, "Procesar otra vuelta").
7. **Consistencia y estándares.** Mismos iconos/colores/etiquetas en toda la app; salidas en
   formatos estándar (CSV/MD/PNG/WebM). El vocabulario de color del HUD debe coincidir con
   `hud-reference.md` (regla de consistencia §8).
8. **Estética y diseño minimalista.** Cada elemento gana su lugar; nada compite con la señal. En el
   HUD esto es crítico: legibilidad sobre el video, jerarquía piloto-vs-referencia (ADR 0005-0007).
9. **Ayuda y documentación en contexto.** Tooltips/captions donde se necesita la decisión, enlaces a
   la guía. La guía visual de export **está incompleta** (imágenes placeholder — C04).
10. **Accesibilidad mínima.** Contraste de texto legible (WCAG AA en lo posible), no depender solo
    del color para transmitir estado (el HUD ya combina color + forma/posición).

---

## 2. El gate de UX/UI (cómo se "aprueban las pruebas de UX")

Tres capas, de menor a mayor autoridad — igual que las barreras de código avisan temprano y
bloquean al final.

### Capa A — Determinista, **BLOQUEA** (en CI, como los tests)

Son verificables por máquina; si fallan, el cambio no debe subir (rojo en CI). Viven junto a la
suite, corren en `pytest`/`verificar.ps1` y en `.github/workflows/tests.yml`.

- **Smoke visual de layout (Playwright).** Screenshot de cada pantalla contra un baseline (Ubuntu =
  verdad canónica, ADR 0012), tolerancia generosa: atrapa "el layout se movió", no antialiasing.
  - *Hoy:* solo cubre el **Paso 0**. **Objetivo:** extender a Pasos 1-4 (con estado/datos
    sintéticos cargados por el harness), un baseline por pantalla.
- **Aserciones estructurales (Streamlit AppTest).** Sin pixeles: que los elementos esperados
  existan (los 3 flujos en el Paso 0, el botón primario de avance, la tabla de vueltas tras cargar,
  el progreso durante el render). Determinista y rápido.
- **Contraste de texto.** Chequeo automatizable de ratio de contraste de los estilos propios
  (los colores del HUD y del CSS de la UI) contra WCAG AA. Es aritmética sobre colores → bloquea.

### Capa B — Juicio, **ACONSEJA** (checkpoint de Mariana, vuelve al PO)

"¿Se ve profesional?", "¿el flujo se siente claro?", "¿el HUD es legible sobre ESTE video?" no son
deterministas. No bloquean por máquina: los dispara el hook de sesión **`mariana-stop`** al tocar
`fantasma/viz/` o `fantasma/ui/`, que **frena el cierre y obliga a mirar** (abrir `fantasma ui` /
revisar el HUD) con esta **checklist**:

- [ ] El cambio respeta las 10 heurísticas de §1 (revisión rápida).
- [ ] La pantalla afectada se ve coherente con el resto (espaciado, tipografía, iconos).
- [ ] El HUD (si aplica) es legible sobre video real, con la jerarquía piloto/ref correcta.
- [ ] Ningún texto en jerga de sistema; vocabulario de pista.
- [ ] Estados visibles: carga, progreso, encoder/tiempo, errores claros.

El resultado de la checklist es **juicio del PO**, no un auto-pase — igual que el Reviewer de código
y el Escribano de docs proponen pero el contenido no bloquea lo irreversible.

### Capa C — Local, **AVISA** (temprano)

`verificar.ps1` corre el smoke visual y las aserciones AppTest en modo aviso antes del push (skipea
limpio si no hay Chromium), como ya hace con lint/formato/tests. El CI es el que bloquea.

> **Regla de oro del gate:** lo que se pueda medir (layout, contraste, presencia de elementos,
> visibilidad de estado) **se mide y bloquea**; lo que sea gusto/sensación **se mira y vuelve al
> PO**. Nunca un gate subjetivo automático.

---

## 3. Estado y plan de implementación

| Pieza del gate | Estado | Acción |
| :-- | :-- | :-- |
| Smoke visual Paso 0 | ✅ existe (ADR 0012); baseline regenerado en v0.14.0 por cambio F-01 | — |
| Smoke visual Pasos 1-4 | ⏸️ diferido | AppTest cubre la estructura; Playwright requiere inyectar estado en browser (no trivial). Diferido post-v1.0 |
| Aserciones AppTest | ✅ Pasos 0-4 cubiertos (`tests/ui/`) — 18 tests en verde (v0.14.0) | — |
| Contraste WCAG | ⏸️ diferido post-v1.0 | Bajo riesgo: paleta reducida, colores revisados a ojo |
| Checklist Mariana | ✅ hook formalizado con los 5 puntos de §2-B (v0.14.0) | — |
| Integración en `verificar.ps1`/CI | ✅ (visual + AppTest vía pytest) | — |

> La decisión de tratar el gate de UX con la dualidad determinismo/juicio se asienta en un ADR
> (ver `docs/decisions/`). Los hallazgos de UX concretos por pantalla se documentan tras el
> diagnóstico con capturas, cruzados con [`casos-de-uso.md`](casos-de-uso.md).

---

## 4. Registro de cambios de patrón por versión

Historial de decisiones de UX que alteraron el layout o el flujo de la UI — para que el baseline visual tenga contexto al regenerarse.

### v0.14.0 (2026-06-30)

**Paso 0 — Rediseño del onboarding y selector de flujo:**
- Hero strip de 3 items (Referencia / Piloto / Salida) sustituye al bloque de texto de intro.
- Tarjetas de flujo con `st.container(border=True, height=260)`: altura fija para alinear los botones de selección entre columnas (ADR 0011).
- Estado neutro para el flujo por defecto: `st.info("Por defecto…")` en vez de `st.success("✓ Seleccionado")` hasta que el usuario confirma explícitamente (F-01). Heurística: **reconocer vs recordar** — el usuario sabe que no eligió nada todavía.
- `st.info`/`st.note` con texto `sgi-note` (borde azul izquierdo) para la instrucción de "una vuelta por flujo / compararse contra sí mismo".

**Paso 2 — Tabla de curvas:**
- Caption de convención de signos reescrito para explicitar que `Diferencia km/h` (+) y `Tiempo ganado/perdido` (+) tienen sentidos opuestos (F-11). Heurística: **prevención de errores** — la ambigüedad anterior llevaba a interpretaciones invertidas.
- Estado vacío cuando `rows=[]` con `st.info` y pasos de diagnóstico (F-10).

**Sidebar:**
- Botón 🔄 Nueva sesión al pie (F-23). Heurística: **control y libertad** — el usuario puede reiniciar sin recargar la pestaña.
