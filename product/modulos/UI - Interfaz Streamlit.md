---
tipo: modulo
clave: UI
dominio: Interfaz de usuario
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# UI - Interfaz Streamlit

## Dominio
- [[Interfaz de usuario]]

## Propósito del módulo
Guiar al usuario paso a paso a través del pipeline completo (importar, comparar, generar overlay, componer video) sin requerir el uso del CLI.

## Alcance
- Paso 0: carga de archivos de telemetría (piloto y referencia).
- Paso 1: configuración de parámetros de comparación.
- Paso 2: comparación y visualización de resultados con avisos del motor y drill-down por curva.
- Paso 3: generación del overlay HUD.
- Paso 4: composición del video final (con aviso temprano si falta ffmpeg).

**No cubre:**
- El CLI como punto de entrada alternativo (siempre disponible y equivalente).
- Instalación del entorno (es `setup.ps1`).

## Regla funcional
La UI es una capa opcional sobre el mismo pipeline que usa el CLI; todo lo que hace la UI es posible desde terminal. Los avisos del motor (autos distintos, delta sospechoso, ffmpeg ausente) deben ser visibles en la UI para que el usuario no interprete un resultado inválido como válido. El análisis de Paso 2 debe priorizar la curva de mayor pérdida y convertirla en acciones concretas sin duplicar lógica del motor.

## Secuencia funcional
- **Módulo anterior:** No aplica (punto de entrada de usuario)
- **Módulo siguiente:** No aplica

## Capacidades
- [[UI-01 - Flujo guiado en pasos]]
- [[UI-02 - Avisos del motor visibles en la UI]]
- [[UI-03 - Drill-down por curva]]

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

## Relacionado con
- [[Interfaz de usuario]]
