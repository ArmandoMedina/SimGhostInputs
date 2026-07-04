---
tipo: modulo
clave: UI-NG
dominio: Interfaz de usuario
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# UI - Interfaz NiceGUI

## Dominio
- [[Interfaz de usuario]]

## Propósito del módulo
Interfaz de usuario principal desde v2.0. App de escritorio NiceGUI (native=True, pywebview) que guía al usuario paso a paso a través del pipeline completo (importar, comparar, generar overlay, componer video) sin requerir el uso del CLI.

## Alcance
- Paso 0: selector de flujo («Solo análisis», «Solo overlay», «Video con HUD»).
- Paso 1: importar laps (telemetría referencia y piloto).
- Paso 2: análisis con avisos del motor y drill-down por curva.
- Paso 3: generación del overlay HUD; checkbox «Al terminar, componer automáticamente» (flujo compose).
- Paso 4: composición del video final (con aviso temprano si falta ffmpeg); opción de mezclar pace notes en el audio; pipeline autónomo (auto-compose desde Paso 3).
- Paso 5: generación del pack de pace notes para CrewChief y mux standalone a video existente.

**No cubre:**
- El CLI como punto de entrada alternativo (siempre disponible y equivalente).
- Instalación del entorno (es `setup.ps1`).

## Regla funcional
La UI NiceGUI es una capa opcional sobre el mismo pipeline que usa el CLI; todo lo que hace la UI es posible desde terminal. AppState en `ng_state.py` gestiona el estado de sesión vía `app.storage.user`, sustituyendo a `st.session_state`. Los avisos del motor (autos distintos, delta sospechoso, ffmpeg ausente) deben ser visibles en la UI para que el usuario no interprete un resultado inválido como válido. El análisis de Paso 2 debe priorizar la curva de mayor pérdida y convertirla en acciones concretas sin duplicar lógica del motor.

## Fuente
- `fantasma/ui/ng_app.py`
- `fantasma/ui/ng_step0.py` … `ng_step5.py`
- `fantasma/ui/ng_state.py` — `AppState` incluye: `last_overlay`, `last_compose_video`, `last_pacenotes`, `auto_compose`, `pending_autocompose`
- `fantasma/ui/ng_helpers.py`

## ADR relacionado
- [ADR 0018 — Framework UI NiceGUI](../../docs/decisions/0018-framework-ui-nicegui.md)

## Secuencia funcional
- **Módulo anterior:** No aplica (punto de entrada de usuario)
- **Módulo siguiente:** No aplica

## Capacidades
- [[UI-01 - Flujo guiado en pasos]]
- [[UI-02 - Avisos del motor visibles en la UI]]
- [[UI-03 - Drill-down por curva]]
- [[UI-04 - Generar pace notes desde la UI]]

## Dependencias funcionales
- [[IMP-MTC - Importador MoTeC]]
- [[IMP-GEN - Importador CSV genérico]]
- [[NRM - Normalización]]
- [[CMP - Comparación]]
- [[COR - Detección de curvas e hitos]]
- [[WER - Desgaste acumulable]]
- [[REP - Reporte y CSVs]]
- [[CHT - Gráficas]]
- [[OVL - Render del overlay]]
- [[CMPO - Composición de video]]
- [[SYN - Auto-sync por audio]]
- [[PAC - Pace Notes CrewChief]]

## Relacionado con
- [[Interfaz de usuario]]
- [[UI - Interfaz Streamlit]]
