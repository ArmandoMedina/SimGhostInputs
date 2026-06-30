---
tipo: capacidad
clave: UI-03
modulo: UI
dominio: Interfaz de usuario
producto: Fantasma
estado: vigente
prioridad: Should Have
---

# UI-03 - Drill-down por curva

## Módulo
- [[UI - Interfaz Streamlit]]

## Propósito funcional
Permitir que el piloto pase de la tabla de tiempo perdido a una instrucción concreta por curva, sin estudiar MoTeC ni revisar manualmente todas las gráficas.

## Actor principal
Usuario que revisa el Paso 2 de `fantasma ui` tras comparar una vuelta contra una referencia.

## Entradas funcionales
- `rows` de `compare()`, ordenadas por `time_lost`.
- `trace` metro a metro con canales `ref_*` y `drv_*`.

## Salidas funcionales
- Selector de curva, con default en la curva de mayor pérdida de tiempo.
- Panel de síntesis con `summary`, plan de ataque y tabla de puntos clave.
- Degradación graceful si faltan canales opcionales (`gear`, `rpm`, `glat`).

## Reglas de negocio
- La curva seleccionada por defecto debe ser la de mayor `time_lost`.
- El panel debe usar `corner_coaching(row, trace)`; la UI no recalcula la lógica de coaching.
- Si el piloto gana tiempo en la curva, el panel debe tratarla como referencia de ejecución, no como problema.
- Los campos dependientes de canales ausentes no se muestran.

## Criterios de aceptación
- Dado que hay varias curvas con pérdidas distintas, cuando se renderiza el Paso 2, entonces el drill-down muestra por defecto la curva con mayor pérdida.
- Dado que una curva no tiene canal `gear`, cuando se renderiza el drill-down, entonces el panel no inventa una marcha y sigue mostrando el resto de señales.
- Dado que una curva no tiene canal `glat`, cuando se renderiza el drill-down, entonces el panel omite G lateral sin lanzar excepción.
- Dado que una curva tiene `time_lost` negativo, cuando se renderiza el drill-down, entonces el mensaje indica que el piloto gana tiempo ahí.

## Dependencias funcionales
- [[CMP-02 - Métricas y flags por curva]]
- [[CMP-01 - Comparar dos vueltas por distancia]]

## Fuera de alcance
- Coaching por LLM.
- Historial entre sesiones.
- Decidir automáticamente si el piloto debe cambiar la trazada completa; el panel solo explica señales medibles.

## Verificación
- `tests/ui/test_step2_avisos.py` · `test_paso2_muestra_drilldown_de_mayor_perdida`.
- `tests/core/test_coaching.py`.

## Relacionado con
- [[Interfaz de usuario]]
