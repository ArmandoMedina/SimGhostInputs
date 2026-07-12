---
tipo: guia
estado: vigente
---
# Mantener el motor al día (el canal de bajada del lazo)

Esta guía es para quien **mantiene un repo con el método instalado** (un "lab"/hijo). El lazo de
sincronización tiene dos sentidos: *la lección sube* (reportas a Jidoka — ver
[`reportar-leccion-a-jidoka.md`](reportar-leccion-a-jidoka.md)) y *la máquina baja* (traes las mejoras del
motor a tu repo). Esto último es lo que aquí se explica.

> **El principio:** la **mecánica** del motor converge a la de Jidoka; tu **instancia** (tu ley
> `blast-radius.json`, tu `product/`, tu `HANDOFF`, tus ADRs) y tus **customizaciones code-first** (tu
> `verificar.ps1` con las herramientas de tu lenguaje, etc.) **nunca se pisan**. El lazo distingue una de otra
> por el **sello** `tools/jidoka-motor.json`.

## El sello: qué recuerda tu repo

`tools/jidoka-motor.json` registra de qué versión de Jidoka viene tu maquinaria y, por pieza, el hash que
Jidoka envió. Campos:

- `version` — la versión de Jidoka a la que sincronizaste por última vez.
- `sembrado_hashes` — hash (normalizado a LF, agnóstico al fin de línea — ADR 0021) por pieza de mecánica.
- `excluir` — *(opcional)* lista de piezas que tu repo **no quiere** (ver más abajo).

## Traer las mejoras: `-Actualizar`

Se corre **desde el repo de Jidoka**, apuntando al tuyo:

```powershell
# (desde el checkout de Jidoka)
./tools/instalar.ps1 -Destino C:\ruta\a\tu-repo -Actualizar
```

Por cada pieza de mecánica, decide con conciencia de tres vías (estilo `dpkg conffiles`) y te lo dice:

| Marca | Qué pasó |
|---|---|
| *(silencio)* / `al dia` | tu pieza es idéntica a la de Jidoka — nada que hacer. |
| `[ACTUALIZA]` | no la habías tocado desde la siembra y Jidoka avanzó → se actualiza. |
| `[NUEVO]` | pieza nueva de esta versión → se agrega. |
| `[DIVERGE]` | **la customizaste** → **no se pisa**; se deja `<pieza>.jidoka-nuevo` al lado para que compares. |
| `[EXCLUIDA]` | está en tu lista `excluir` → no se toca ni se re-agrega. |

Tu **instancia** (ley, `product/`, `HANDOFF`, ADRs) no se itera nunca: `-Actualizar` solo toca `mecanica`.

### Manejar las divergencias

Cada `[DIVERGE]` deja un sidecar `<pieza>.jidoka-nuevo` con la versión de Jidoka. Revisa el diff y decide:

- **Adoptar** la de Jidoka (si tu "customización" era en realidad una versión atrasada):
  `Move-Item <pieza>.jidoka-nuevo <pieza> -Force`.
- **Conservar** la tuya (si es una customización genuina de tu lenguaje): borra el sidecar
  (`Remove-Item <pieza>.jidoka-nuevo`).
- Reconciliar a mano, o mover tu ajuste a la costura `.local` (p.ej. `tools/verificar.local.ps1`), para que la
  mecánica converja sin bifurcarse.

> **Los `.jidoka-nuevo` son andamio de reconciliación, no herramienta terminada: bórralos antes de commitear.** En
> cualquiera de los tres caminos, el sidecar desaparece del árbol una vez que decidiste — lo que entra al diff del PR
> es tu decisión *aplicada* (adoptaste, conservaste o reconciliaste), nunca el `.jidoka-nuevo` en sí.

**Corre siempre en una rama, revisa el diff, ábrelo como PR** — el diff ES la revisión. Y **corre tu suite de
tests antes de mergear** (el motor bajado no vale hasta que corre verde en tu repo).

## Rechazar piezas que no quieres: `excluir`

Si una pieza del núcleo no encaja en tu repo (p.ej. un `probar-gate.ps1` genérico incompatible con tu
`verificar` code-first, o un `andon.yml` que duplica tu CI), **declárala** en tu sello para que el lazo deje de
re-agregarla en cada bajada (ADR 0022). En `tools/jidoka-motor.json`:

```json
{
  "version": "1.5.1",
  "sembrado_hashes": { "...": "..." },
  "excluir": [
    "tools/probar-gate.ps1",
    ".github/workflows/andon.yml"
  ]
}
```

A partir de ahí, `-Actualizar` reporta esas piezas como `[EXCLUIDA]` y no las toca. La lista se **preserva**
entre bajadas (no la pierdes al re-sincronizar). Sin `excluir`: comportamiento normal (nada cambia).

## Ver la divergencia fina: `estado-motor -Detallado`

La versión del sello es de grano grueso. Para ver **qué piezas divergen** de Jidoka, por hash:

```powershell
# (desde tu repo)
./tools/estado-motor.ps1 -Jidoka C:\ruta\a\jidoka -Detallado
```

Lista las `[DIVERGE]` y `[AUSENTE]`, y cuenta las al día. Es **aviso, no muro** (nunca bloquea; exit 0). Sin
`-Jidoka`, o con `$env:JIDOKA_HOME` exportado, solo compara la versión.

## Sellar un repo que convergió a mano: `-Sellar`

Si adoptaste el método a mano y **no tienes sello** (o quieres re-crearlo bien), `-Sellar` lo escribe
clasificando cada pieza contra el Jidoka actual (ADR 0019):

```powershell
# (desde Jidoka)
./tools/instalar.ps1 -Destino C:\ruta\a\tu-repo -Sellar
```

- pieza **idéntica** a Jidoka → **pristina**: se registra (el próximo `-Actualizar` la mantiene al día).
- pieza **distinta** → **customizada**: se omite de la semilla (el próximo `-Actualizar` la ve `[DIVERGE]` y la
  preserva).

> **Ojo:** `-Sellar` compara contra el Jidoka **actual**. Úsalo cuando tu repo está **al nivel** de ese Jidoka
> (convergido a mano). Si tu repo está **atrasado**, no uses `-Sellar` (marcaría como "customizada" cualquier
> pieza pristina-pero-vieja): usa `-Actualizar`, que se apoya en el sello existente.

## Para el mantenedor de Jidoka: cortar un release con `publicar.ps1`

*(Solo el repo Jidoka; no se siembra.)* El release se **deriva del SSOT** `tools/version.txt` (ADR 0020):

```powershell
./tools/publicar.ps1              # corre la suite, crea el tag + release con las notas del CHANGELOG
./tools/publicar.ps1 -DryRun      # muestra qué haría sin crear nada
./tools/publicar.ps1 -SoloVerificar   # corre el preflight (suite) sin publicar
```

Escribe la versión **una vez** en `version.txt` (y su sección en el CHANGELOG); el tag, el título y las notas
derivan de ahí. No publica si un self-test falla.

---

> **Fin de línea:** el hash del motor es agnóstico al EOL (normaliza a LF antes de comparar), así que tu repo
> puede tener la política que quiera (`eol=lf` o `crlf`) y el lazo reconcilia por **contenido**, no por bytes
> (ADR 0021).
