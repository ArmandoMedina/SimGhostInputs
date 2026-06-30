---
tipo: backlog
producto: Fantasma
estado: vigente
---

# Backlog — Ítems diferidos post-v1.0

> Esta es la **bandeja de entrada de lo diferido**: requerimientos que se conocen, están investigados (algunos con spec completa) y se retomarán después de declarar estable la v1.0. El detalle vivo de cada uno vive en su documento dueño (ROADMAP o ADR); aquí solo se registra el qué y el puntero al dueño. No duplicar el contenido de esos documentos.

---

## Ítems diferidos

### Front de escritorio custom (v2.0)
Evaluar migrar la UI de Streamlit a un front con instalación doble-click (candidatos: Tauri, pywebview, Electron) que supere los dos límites reales detectados: personalización topada y fricción de instalación. No es una migración decidida: es una evaluación con gatillo antes de comprometerse.
- Dueño: [ROADMAP §Diferido — Front de escritorio custom](../../ROADMAP.md) · [ADR 0010](../../docs/decisions/0010-framework-ui-streamlit.md)

### Coaching de voz — CrewChief Pace Notes
Generar archivos de pace notes (WAV de tonos + voz opcional) ubicados en los metros exactos de las curvas del `corners.json`, compatibles con el sistema nativo de CrewChief. Spec completa disponible.
- Dueño: [ROADMAP §Diferido — CrewChief Pace Notes](../../ROADMAP.md) · [ADR 0002](../../docs/decisions/0002-crewchief-pacenotes.md)

### Drill-down por curva
Convertir la tabla de tiempo perdido en coaching accionable: el piloto selecciona una curva y ve qué corregir (delta de frenada, V-Min target, delta de gas), con síntesis en lenguaje natural. Aritmética pura sobre `corners_compare.csv`.
- Dueño: [ROADMAP §Diferido — Drill-down por curva](../../ROADMAP.md) · [PRODUCT_BRIEF §10](../../PRODUCT_BRIEF.md)

### Histórico entre sesiones
Comparar el rendimiento en una misma curva a lo largo de varias tandas para detectar progreso, techo o retroceso. Requiere modelo `SessionHistory` y almacenamiento local (SQLite o directorio de JSONs).
- Dueño: [ROADMAP §Diferido — Histórico entre sesiones](../../ROADMAP.md)

### Nuevos importadores
Importadores nativos de `.ld` (MoTeC), `.ibt` (iRacing) y ampliación de `GUESS`/`MOTEC_MAP` para SimHub, ACC y rF2. Elimina la dependencia de MoTeC i2 como intermediario.
- Dueño: [ROADMAP §Diferido — Nuevos importadores](../../ROADMAP.md)

### fantasma-live (repo separado)
Coaching adaptativo en tiempo real vía UDP desde AMS2: listener a 60 Hz, comparador en vivo, motor de voz TTS con latencia menor a 200ms. Solo si Pace Notes no cubre el caso de uso.
- Dueño: [ROADMAP §Diferido — fantasma-live](../../ROADMAP.md)

### Lista de vueltas procesadas en la sesión (UI)
Tabla acumulada en la UI de vuelta, salida y calidad de sync para quien procesa varias telemetrías seguidas en la misma sesión. Conveniencia, no corrección.
- Dueño: [ROADMAP §Diferido — Lista de vueltas](../../ROADMAP.md)
