# Lección (draft) — El mandato "evidencia 100% sintética" necesita reconocer el patrón "excepción de dominio con nombre"

> Draft para revisión humana antes de presentar como issue a Jidoka. Formato del template
> `leccion.md`. Anonimizado (frontera-nda). **No presentado aún.**

## La lección, en una frase

El asiento revisor-visual manda "evidencia 100% sintética", pero hay dominios donde lo sintético
**no ejercita lo que se está probando** — y forzar la regla al pie degrada la QA en vez de
protegerla; el método debería reconocer explícitamente el patrón "**excepción de dominio con
nombre**" (doctrina/07) como la salida legítima, no como una violación tolerada.

## Dónde la pagaste

Caso de un proyecto con **HUD/render visual sobre telemetría**. La QA visual de aceptación necesita
que el render se vea como en producción; los datos **sintéticos no reproducen el comportamiento real
del render** (curvas, densidad, casos límite reales), así que la captura sintética "pasa" sin
ejercitar de verdad el pixel que el cliente va a mirar. Lo que la regla *realmente* protege —que
**ningún dato real entre al repo**— sí se puede cumplir por otra vía: la telemetría real vive **fuera
del repo** (ruta gitignoreada) y en `qa_runs/` solo se commitean **capturas** renderizadas, nunca
telemetría cruda. Se resolvió documentándolo como **excepción de dominio con nombre** (patrón Jidoka
`doctrina/07`), no forzando a sintético. Registrado en el ADR de homologación de este repo.

## Qué haría Jidoka distinto

Que la doctrina del asiento revisor-visual **nombre el patrón de escape**: "evidencia 100% sintética
*salvo excepción de dominio con nombre*, cuando (a) lo sintético no ejercita el artefacto bajo prueba
y (b) el invariante que la regla protege —que ningún dato real se commitee— se satisface por otra
vía verificable (dato real fuera del repo, solo artefactos derivados dentro)". Así el revisor-visual
no queda entre romper la práctica o romper la regla: tiene una tercera opción **prescrita y
auditable**. Regla 2-3: este es **un uso real** (queda esperando su segundo antes de volverse regla).
