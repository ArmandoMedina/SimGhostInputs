# Lección (draft) — `probar-gate.ps1` no se pudo portar sin `-Cambiados`: ítem de convergencia (bajada)

> Draft para revisión humana antes de presentar como issue a Jidoka. Formato del template
> `leccion.md`. Anonimizado (frontera-nda). **No presentado aún.**
>
> **Nota de tipo:** esta NO es una lección que Jidoka deba absorber — Jidoka **ya la resolvió**.
> Es un ítem de **convergencia (bajada)**: SGI debería adoptar la capacidad vía el lazo. Se registra
> aquí porque **valida el lazo**: una brecha real de método que ahora tiene mecanismo para cerrarse.

## La lección, en una frase

El self-test del gate (`probar-gate.ps1`) exige que `verificar.ps1` acepte **inyección de la lista de
archivos cambiados** (`-Cambiados`) para probarse sin depender de git; un hijo cuyo gate no tiene esa
costura **no puede portar el self-test** — y arreglarlo implica editar el propio gate, que un pase
autónomo tiene vedado.

## Dónde la pagaste

Caso de un repo que convergió su motor a Jidoka **a mano** (no por el instalador). Al intentar traer
`probar-gate.ps1`, su `verificar.ps1` local no aceptaba `-Cambiados` (inyectar una lista de archivos
sin consultar git), que es justo lo que el self-test necesita para simular un cambio y comprobar que
el gate bloquea/avisa lo correcto. Portarlo obligaba a **editar el gate mismo** — la regla del método
reserva tocar el gate a una sesión humana, no a un pase autónomo. Quedó diferido en el ADR de
homologación y anotado en el ROADMAP.

## Qué haría Jidoka distinto

**Nada nuevo del lado del método: Jidoka ya lo tiene resuelto.** Verificado leyendo
`tools/verificar.ps1` de Jidoka (0.10.1-beta): expone `[string[]]$Cambiados = @()` y
`if ($Cambiados.Count -gt 0) { $changed = $Cambiados }`, y trae `tools/probar-gate.ps1`. Lo que este
caso demuestra es que **el lazo es el mecanismo correcto**: en vez de que el hijo parchee su gate a
mano (divergencia), la capacidad **baja** desde Jidoka con `./tools/instalar.ps1 -Actualizar`,
re-sembrando `verificar.ps1` (o dejándolo al lado como `.jidoka-nuevo` para reconciliar, porque el
`verificar.ps1` del hijo diverge por dominio: ruff/pytest). El valor de registrarlo: es una **brecha
real** (no hipotética) que ahora tiene ruta de cierre — la mejor evidencia de que el lazo sirve.
Regla 2-3: **un uso real**, esperando su segundo.
