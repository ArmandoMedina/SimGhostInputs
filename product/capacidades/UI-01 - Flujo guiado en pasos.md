---
tipo: capacidad
clave: UI-01
modulo: UI
dominio: Interfaz de usuario
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# UI-01 - Flujo guiado en pasos

## Módulo
- [[UI - Interfaz Streamlit]]

## Propósito funcional
Guiar al usuario a través del pipeline completo (cargar archivos, comparar, generar overlay, componer video) mediante una interfaz web paso a paso sin requerir el CLI.

## Actor principal
Usuario (piloto o ingeniero de datos) que abre la app con `fantasma ui`.

## Entradas funcionales
- Archivos de telemetría (referencia y piloto) cargados en el Paso 0.
- Parámetros de análisis seleccionados en cada paso.

## Salidas funcionales
- Resultados del análisis visibles en el navegador.
- Archivos generados (report.md, CSVs, PNG, video) en el directorio de salida.

## Reglas de negocio
- La aplicación Streamlit (`app.py`) debe inicializar sin excepción cuando streamlit está instalado.
- El router de pasos (`nav_step` en session_state) determina qué paso se renderiza.
- Todo lo que hace la UI es equivalente a lo que ofrece el CLI.

## Criterios de aceptación
- Dado que streamlit está instalado, cuando se ejecuta `app.py` vía `AppTest`, entonces la aplicación inicializa sin lanzar ninguna excepción.

## Dependencias funcionales
- [[IMP-MTC-01 - Importar CSV de MoTeC i2]]
- [[IMP-GEN-01 - Importar CSV genérico con mapeo]]
- [[NRM-03 - Remuestrear por distancia]]
- [[CMP-01 - Comparar dos vueltas por distancia]]

## Fuera de alcance
- Front de escritorio custom (diferido a v2.0 según ADR 0010).

## Verificación
- Cubierta por `tests/ui/test_app_smoke.py` (`test_app_starts_without_exception`).

## Relacionado con
- [[Interfaz de usuario]]

> **Nota:** El test `test_app_starts_without_exception` cubre únicamente que la app arranca; los criterios de los pasos individuales están en [[UI-02 - Avisos del motor visibles en la UI]].
