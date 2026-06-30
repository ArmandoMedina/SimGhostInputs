---
tipo: capacidad
clave: <FAM-MOD-NN, ej. IMP-MTC-01>
modulo: <módulo al que pertenece>
dominio: <dominio>
producto: <producto o solución>
estado: en_definicion
prioridad: Must Have
---

# <CLAVE> - <Nombre de la capacidad>

## Módulo
- [[<módulo>]]

## Propósito funcional
<Qué permite hacer el sistema y para qué. Una o dos frases de comportamiento esperado.>

## Actor principal
<Quién o qué dispara la capacidad: Sistema, Usuario, el CLI, un paso de la UI…>

## Entradas funcionales
<Qué datos o condiciones necesita para ejecutarse.>
- <Entrada 1.>

## Salidas funcionales
<Qué produce: datos, archivos, estatus.>
- <Salida 1.>

## Reglas de negocio
<Las reglas que el sistema debe cumplir. Cada una concreta y verificable, suficiente para implementar sin inventar nada.>
- <Regla 1.>

## Excepciones
<Qué pasa cuando algo sale del camino feliz. (Opcional, pero clave en flujos críticos.)>
- **<Caso de excepción>:** <qué debe hacer el sistema.>

## Criterios de aceptación
<Cómo se verifica que las reglas se cumplen. Formato Gherkin. Idealmente, cada criterio se automatiza como una prueba (ver engineering/pruebas.md) — el test ES el criterio, ejecutable.>
- Dado que <contexto>, cuando <acción>, entonces <resultado esperado>.

## Dependencias funcionales
- <Otra capacidad, componente o decisión pendiente de la que depende.> o `No aplica`

## Fuera de alcance
<Qué NO cubre esta capacidad — y, si ayuda, a qué otra capacidad pertenece.>
- <Tema fuera de alcance.>

## Relacionado con
- [[<módulo>]]

<!--
Campos del frontmatter:
  tipo: capacidad
  clave      → identificador estable FAM-MOD-NN (no cambia aunque se renombre)
  modulo, dominio, producto  → su lugar en la jerarquía
  estado     → en_definicion | en_revision | vigente | pausado | fuera_de_alcance
  prioridad  → Must Have | Should Have | Could Have | Won't Have | Por definir

Disciplina escala con el riesgo: bastan Propósito + Reglas de negocio + Criterios de
aceptación. Las demás secciones se llenan cuando el flujo es crítico. Una capacidad NUNCA
se revisa aislada: siempre contra su módulo, dominio y alcance. Borra este comentario.
-->
