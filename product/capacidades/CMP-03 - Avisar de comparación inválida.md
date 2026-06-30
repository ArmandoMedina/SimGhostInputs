---
tipo: capacidad
clave: CMP-03
modulo: CMP
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CMP-03 - Avisar de comparación inválida

## Módulo
- [[CMP - Comparación]]

## Propósito funcional
Detectar automáticamente situaciones donde la comparación produce un resultado numérico pero probablemente inválido (circuito diferente, auto diferente) y emitir avisos que el sistema muestra al usuario.

## Actor principal
Sistema (parte de `compare()`, ejecutada al finalizar el cálculo del delta).

## Entradas funcionales
- Summary con `total_delta` y `ref_laptime`.
- Metadatos Vehicle de referencia y piloto.

## Salidas funcionales
- `summary["avisos"]`: lista de strings con los avisos emitidos (puede estar vacía).

## Reglas de negocio
- Si `total_delta` supera el 50% del `ref_laptime`, se añade un aviso de "delta sospechosamente grande".
- Si ambas vueltas tienen metadato `Vehicle` con valores distintos, se añade un aviso de "autos distintos".
- Si `Vehicle` está ausente en alguna de las vueltas, no se emite aviso de autos (degradación graceful).
- Un delta normal y mismo auto no generan ningún aviso.

## Criterios de aceptación
- Dado que el delta acumulado supera el 50% del tiempo de vuelta de la referencia (posible circuito distinto), cuando se comparan, entonces `summary["avisos"]` contiene un aviso que incluye la frase "sospechosamente grande".
- Dado que referencia y piloto tienen metadato `Vehicle` con valores distintos, cuando se comparan, entonces `summary["avisos"]` contiene un aviso que incluye "autos distintos".
- Dado que el delta es normal y los autos son iguales (o `Vehicle` está ausente), cuando se comparan, entonces `summary["avisos"]` está vacío.
- Dado que el Paso 2 de la UI recibe un summary con aviso de autos distintos, cuando se renderiza, entonces el aviso es visible como widget de advertencia (`st.warning`).

## Dependencias funcionales
- [[CMP-01 - Comparar dos vueltas por distancia]]

## Fuera de alcance
- Validación del circuito por geometría o nombre de pista (no implementado).

## Relacionado con
- [[Normalización y comparación]]
- [TEC-CMP-01 — Comparación por distancia](../../engineering/especificaciones/TEC-CMP-01%20-%20Comparacion%20por%20distancia.md)
