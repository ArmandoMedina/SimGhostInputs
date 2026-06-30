---
tipo: modulo
clave: COR
dominio: Detección de curvas e hitos
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# COR - Detección de curvas e hitos

## Dominio
- [[Detección de curvas e hitos]]

## Propósito del módulo
Detectar las curvas de una vuelta por mínimo de velocidad (V-Min) y extraer sus hitos relevantes: ápex, inicio de frenada, punto de aplicación de gas y, si el canal glat está disponible, el G-lat máximo.

## Alcance
- Detección de curvas mediante eventos V-Min sobre el perfil de velocidad por distancia.
- Extracción de hitos por curva: apex, brake_start, y opcionalmente gas_start y g_lat_max.
- Clasificación de dirección de curva (left / right).

**No cubre:**
- Comparación de curvas entre piloto y referencia (es [[CMP - Comparación]]).
- Análisis de desgaste de gomas (es [[WER - Desgaste acumulable]]).

## Regla funcional
El canal `speed` es obligatorio; sin él la detección falla con `ValueError`. La detección V-Min es el criterio principal, independiente de la disponibilidad de `glat`.

## Secuencia funcional
- **Módulo anterior:** [[NRM - Normalización]]
- **Módulo siguiente:** [[CMP - Comparación]]

## Capacidades
- [[COR-01 - Detectar curvas e hitos]]

## Dependencias funcionales
- [[NRM - Normalización]]

## Relacionado con
- [[Detección de curvas e hitos]]
- [TEC-COR-01 — Detección de curvas e hitos](../../engineering/especificaciones/TEC-COR-01%20-%20Deteccion%20de%20curvas%20e%20hitos.md)
