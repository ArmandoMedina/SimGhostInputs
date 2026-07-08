---
tipo: capacidad
clave: UI-04
modulo: UI
dominio: Interfaz de usuario
producto: Fantasma
estado: vigente
prioridad: Should Have
---

# UI-04 - Generar pace notes desde la UI

## Módulo
- [[UI - Interfaz NiceGUI]]

## Propósito funcional
Permitir al usuario generar el pack de pace notes para CrewChief (tonos, voz o ambos) y aplicar ese audio a un video existente desde el Paso 5 del wizard NiceGUI, sin necesidad de usar el CLI.

## Actor principal
Usuario (piloto o ingeniero de datos) que llega al Paso 5 desde el botón «Generar Pace Notes» del análisis del Paso 2.

## Entradas funcionales
- `state.rows` y `state.corners` — resultado del análisis del Paso 2 (requerido para generar el pack).
- Modo de generación: `tones`, `voice` o `both`.
- Top-N curvas a cubrir (default 5, máx. 99) o checkbox «Todas las curvas» (manda `top=0`, pace notes de ritmo — [ADR 0024](../../docs/decisions/0024-sincronia-pace-notes.md)).
- Volumen (0.1–1.0).
- Idioma (solo en modo voz/ambos): `es-MX`, `es-ES`, `en-US`.
- Directorio de salida (pre-rellenado con la ruta de CrewChief detectada por `crewchief_pacenotes_dir(track)`).
- Para mux standalone: video existente + carpeta del pack + vuelta del piloto (`state.drv_lap`) + ruta de salida opcional.
- Selección y prioridad de cues del catálogo (`enabled`/`priority` por tipo, resuelto por [[PAC-02 - Plan anti-saturacion de senales]]) y perfil a cargar/guardar/importar — ver [ADR 0027](../../docs/decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md) y la guía de usuario (Paso 5, «Cues: selección y prioridad»).

## Salidas funcionales
- Pack de pace notes generado en el directorio de CrewChief (delegado a `build_pack` de [[PAC-01 - Generar pack de pace notes CrewChief]]).
- `state.last_pacenotes` actualizado con el directorio de salida (marca el Paso 5 como completado en el sidebar).
- Video con audio de pace notes mezclado, sin re-encodear el stream de video (mux standalone vía `mux_pace_notes_into_video`).

## Reglas de negocio
- Si `state.rows` o `state.corners` no están disponibles, el panel ① del Paso 5 muestra un aviso con botón de vuelta al Paso 2 en lugar del formulario de generación; el panel ② permanece visible y operativo independientemente del estado del análisis.
- La generación del pack se ejecuta en `run.io_bound` para no bloquear el event loop de NiceGUI.
- El directorio de destino se pre-rellena con `crewchief_pacenotes_dir(track_name)` si el metadato del circuito está disponible en la vuelta de referencia.
- El modo `voice` y `both` muestran el selector de idioma; el modo `tones` lo oculta.
- El mux standalone usa `mux_pace_notes_into_video` (ffmpeg `-c:v copy`); no re-encodea el video.
- El botón «Aplicar sonido» se deshabilita hasta que estén rellenos el video, la carpeta del pack, y `state.drv_lap` esté cargada; mientras está deshabilitado, un caption bajo el botón lista exactamente qué falta.
- El panel ① incluye una leyenda plegable de tonos derivada del motor (`PLAN_CUES`/`DEFAULT_FREQS`/`COUNTDOWN_SCALE`/`DEFAULT_COUNTDOWN_S` — DRY: si el motor cambia, la leyenda no miente), con la aclaración de que los tonos marcan los puntos de la vuelta de referencia.
- Si el video elegido en ② trae sidecar `.sync.json` (ADR 0024), la UI lo coteja con `compose.sync_sidecar_mismatch` (la misma fuente que usa el mux para negarse) y muestra ✓ verde o ⚠ amarillo antes de apretar el botón.
- El panel ① expone además cada tipo de cue del catálogo (`DEFAULT_CONFIG` de `pacenotes.py`) como fila `enabled`+`priority`; los perfiles se cargan, guardan e importan como JSON portable en `~/.simghostinputs/cue-profiles/`, con degradación con gracia ante perfiles inválidos o de terceros (nunca crashea el paso).

## Criterios de aceptación
- Dado que `state.rows` o `state.corners` es None, cuando se renderiza el Paso 5, entonces el panel ① muestra el aviso de "falta el análisis" y el botón de vuelta al Paso 2 en lugar del formulario de generación; el panel ② («Aplicar sonido a un video existente») permanece visible y usable.
- Dado que `state.rows` y `state.corners` están disponibles, cuando el usuario pulsa «Generar Pace Notes», entonces se muestra un spinner y al terminar `state.last_pacenotes` se actualiza con el directorio de salida.
- Dado que la generación termina con éxito, cuando se actualiza `state.last_pacenotes`, entonces el Paso 5 aparece como completado (✅) en el sidebar.
- Dado que `state.drv_lap` es None, cuando se renderiza el panel de mux, entonces el botón «Aplicar sonido» está deshabilitado.
- Dado que `state.drv_lap`, el video y la carpeta del pack están rellenos, cuando el usuario pulsa «Aplicar sonido», entonces se ejecuta `mux_pace_notes_into_video` en background y se notifica al completar.
- Dado que falta alguna de las tres entradas del mux, cuando se renderiza el panel ②, entonces el caption bajo el botón lista exactamente cuáles faltan.
- Dado que el usuario marca «Todas las curvas», cuando genera el pack, entonces se usa `top=0` y el campo Top N queda deshabilitado.
- Dado un video con sidecar `.sync.json` de otra vuelta, cuando el usuario lo elige en ②, entonces aparece el aviso ⚠ con la vuelta esperada y el mux se niega con error accionable.
- Dado que el usuario pulsa «🔔 Generar Pace Notes» en el Paso 2, cuando el análisis está disponible, entonces la app navega al Paso 5 (regresión QA 2026-07-05: el `navigate` async sin await no navegaba).

## Dependencias funcionales
- [[PAC-01 - Generar pack de pace notes CrewChief]]
- [[UI-01 - Flujo guiado en pasos]]

## Fuera de alcance
- La lógica de generación de audio del pack — es [[PAC-01 - Generar pack de pace notes CrewChief]].
- El mux durante la composición del Paso 4 — es parte de [[CMPO-01 - Componer video con ffmpeg (NVENC + fallback)]].

## Verificación
- `tests/ui/test_ng_step5.py` — `test_step5_heading_visible`, `test_step5_guard_without_analysis`, `test_step5_apply_btn_disabled_without_drv_lap`.

## Relacionado con
- [[Interfaz de usuario]]
- [[PAC - Pace Notes CrewChief]]
