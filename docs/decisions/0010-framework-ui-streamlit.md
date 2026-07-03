# ADR 0010 — Framework de UI: Streamlit en v1.0; front de escritorio custom diferido a v2.0

- **Estado:** Aceptada
- **Fecha:** 2026-06-26

## Contexto

La UI del proyecto (`fantasma/ui/`) está construida en **Streamlit** desde el inicio,
pero esa elección **nunca se registró como decisión** — era arquitectura de facto. Una
sesión futura (u otra IA) que viera las limitantes de personalización de Streamlit
podría plantear migrar el front sin entender por qué se eligió ni qué restricciones
debe respetar al hacerlo.

Hechos y restricciones que enmarcan la decisión:

- El proyecto es una **herramienta local, offline, de un solo usuario**, escrita en
  Python (pandas/numpy/matplotlib). Su lógica vive en `core/`; la UI es una capa
  delgada que llama a `core/` y dispara los pasos del pipeline ("CLI primero").
- Lo mantiene **una persona que vibe-codea y no es programadora web**: el costo de
  escribir/sostener HTML/CSS/JS a mano es real y recurrente.
- Durante el desarrollo han aparecido **limitantes de personalización** del front en
  Streamlit (layout, estilo, control fino de la presentación).
- Una meta del producto es que **el usuario final no batalle** para usarlo.

## Decisión

La UI de **v1.0 es Streamlit**. Un front de escritorio **custom queda diferido a v2.0**,
sujeto a evaluación (ROADMAP) y no decidido aún en su arquitectura.

## Razones

- **Reusa `core/` directo, sin capa intermedia.** Streamlit corre Python en el mismo
  proceso; la UI llama a las funciones del núcleo sin API ni serialización. Un front web
  exigiría exponer `core/` por HTTP — trabajo y superficie de error que hoy no existen.
- **Cero front-end web para construir.** Sin HTML/CSS/JS ni paso de build. Para quien no
  programa web, eso es la diferencia entre avanzar y atascarse.
- **Encaja con la forma de la app.** La UI es formularios + gráficas + disparar pasos
  del pipeline. Ese es exactamente el caso de uso de Streamlit; no se está construyendo
  una web app rica que justifique el costo de un front propio.
- **Permitió llegar a v1.0.** El foco de la 1.0 es *estabilizar/validar el pipeline
  existente*, no construir UI. Streamlit no compite por ese tiempo.

## El camino que NO se toma (y por qué tienta)

- **Front HTML desde cero AHORA.** Tienta porque resolvería las limitantes de
  personalización y haría el front testeable con Playwright como en otros repos (mockups
  HTML estáticos). Se descarta para v1.0 porque: (1) reescribir la UI es lo contrario de
  *estabilizar*, que es la meta declarada de la 1.0; (2) un HTML desde cero **no resuelve
  solo** — necesita además exponer `core/` (servidor local o shell de escritorio), que es
  el trabajo de fondo; (3) la superficie de UI (pasos 0→4) es chica y acotada, así que
  migrar **después** no es más caro que ahora — *mientras* `core/` siga desacoplado.
- **Quedarse en Streamlit para siempre por inercia.** También tienta (no tocar lo que
  funciona), pero ignora una limitante real: Streamlit le pone **techo a la
  personalización** y a la fricción de instalación (ver Consecuencias). Por eso la
  migración no se cancela, se **difiere con gatillo**, no se entierra.
- **Para la migración: web-en-navegador con servidor local (FastAPI) en vez de shell de
  escritorio empaquetado.** Tienta por ser "más estándar". Pero **no reduce la fricción
  del usuario**: seguiría necesitando Python + terminal + un `setup.ps1`, igual que hoy.
  Un **shell de escritorio empaquetado** (Tauri / pywebview + empaquetado) compila a un
  `.exe` de doble-click — *menos* fricción que Streamlit, no más. Si se migra, esa es la
  dirección a favorecer (a confirmar con benchmark, no decidido aquí).

## Consecuencias

**Se gana:** velocidad de construcción, reuso directo de `core/`, foco de v1.0 intacto.

**Se acepta como límite (gatillo para revisitar en v2.0):**
- **Personalización del front** topada por Streamlit.
- **Fricción de instalación:** Streamlit no es realmente "doble-click" — exige Python +
  terminal + `setup.ps1` para taparlo. Le pone techo a qué tan fácil de instalar puede ser.

**Restricciones que mantienen barata la futura migración:**
- **Mantener `core/` desacoplado de la UI.** Es lo que mantiene plano el costo de migrar:
  si la lógica se enreda con Streamlit, migrar se vuelve caro. Proteger esa frontera.
- **Testing a prueba de migración.** Preferir **AppTest** (lógica de los flujos 0→4) y
  **snapshot de imagen del HUD** (la salida visible del producto) sobre **Playwright
  sobre Streamlit**: los selectores de Playwright contra el DOM de Streamlit se tirarían
  al migrar el front, mientras que AppTest (Python) y el snapshot del HUD (output)
  sobreviven. Playwright se reserva para el front nuevo, donde el markup es controlado.

**Pendiente de validar (v2.0):** la **arquitectura** del front custom (shell de escritorio
empaquetado vs otras) **no está decidida** — se resuelve con el benchmark apuntado en el
ROADMAP. Este ADR fija *que* se difiere y *con qué restricciones*, no *cuál* tecnología.

## Enmiendas

- **2026-06-30 — [ADR 0018](0018-framework-ui-nicegui.md):** la evaluación del front custom
  pendiente de v2.0 queda resuelta. La UI de v2.0 migra a **NiceGUI** (MIT) con
  `nicegui-pack` + Inno Setup. Ver ADR 0018 para la decisión completa y las restricciones
  que hereda de este ADR. El estado de este ADR pasa a **Parcialmente reemplazada por ADR 0018**
  en lo que respecta a la arquitectura del front de v2.0; las restricciones de `core/`
  desacoplado y testing a prueba de migración se honran y se detallan en ADR 0018.

- **2026-06-28 — [ADR 0012](0012-playwright-smoke-visual-ui.md):** la restricción de
  testing de arriba ("Testing a prueba de migración": no Playwright sobre Streamlit) queda
  **acotada**. Sigue valiendo para la *lógica* de los flujos 0→4 (eso lo cubre AppTest,
  que sobrevive a la migración), pero **no** para el **smoke visual**: el ADR 0012 adopta
  Playwright para un snapshot de imagen acotado de las pantallas clave en CI. El motivo es
  que aquí se asumía la migración del front *cerca* (la prueba moriría pronto); el PO
  confirmó que es de **meses**, así que la cobertura se amortiza y el cálculo se invierte.
  Además, AppTest no ve píxeles, por lo que no atrapa bugs de layout como el del Paso 0.
