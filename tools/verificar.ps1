#Requires -Version 5
# verificar.ps1 - Pipeline de barreras deterministas local. Se corre ANTES de subir:
# lint (ruff) + formato (ruff format) + tests (pytest) + doc-gate + auditor del grafo.
# Inspirado en el patron "no-mistakes" (convenciones de metodo: project-starter).
# lint/formato/tests AVISAN (el CI los hace cumplir); el doc-drift de la seccion 8
# (core/->formato-datos, viz/->hud-reference) y los hallazgos BLOQUEA del auditor del
# grafo de docs (auditar.ps1: wikilinks rotos, frontmatter, criterios) BLOQUEAN el
# push (exit 1) - poka-yoke.
# Saltar a proposito: git push --no-verify.
#
# Uso:  ./tools/verificar.ps1
#
# Nota: archivo ASCII a proposito (sin acentos) para no depender del BOM en PS 5.1.

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$script:warn = 0
$script:block = 0

function Note($msg)  { Write-Host "  [AVISO] $msg"   -ForegroundColor Yellow; $script:warn++ }
function Block($msg) { Write-Host "  [BLOQUEA] $msg" -ForegroundColor Red;    $script:block++ }
function Ok($msg)    { Write-Host "  [OK] $msg"      -ForegroundColor Green }

Write-Host "== Verificar (modo aviso; el CI es el que bloquea) =="

# 1. Lint -------------------------------------------------------------------
Write-Host "`n-- Lint (ruff check) --"
ruff check . | Out-Host
if ($LASTEXITCODE -eq 0) { Ok "sin hallazgos de lint" }
else { Note "ruff check encontro algo (arriba). Arreglo seguro: ruff check . --fix" }

# 2. Formato ----------------------------------------------------------------
Write-Host "`n-- Formato (ruff format --check) --"
ruff format --check . | Out-Host
if ($LASTEXITCODE -eq 0) { Ok "formato consistente" }
else { Note "archivos sin formatear. Aplicar: ruff format .  (ver docs/benchmark-linter.md)" }

# 3. Tests ------------------------------------------------------------------
Write-Host "`n-- Tests (pytest) --"
$env:PYTHONPATH = $repo
pytest | Out-Host
if ($LASTEXITCODE -eq 0) { Ok "tests verdes" }
else { Note "pytest fallo (arriba). Un rojo se diagnostica, no se silencia." }

# 4. Doc-gate: codigo tocado sin CHANGELOG ----------------------------------
Write-Host "`n-- Doc-gate (CHANGELOG) --"
$upstream = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
if ($LASTEXITCODE -eq 0) { $changed = git diff --name-only '@{u}..HEAD' }
else { $changed = git diff --name-only HEAD }
$tocoCodigo    = $changed | Where-Object { $_ -like 'fantasma/*' }
$tocoChangelog = $changed | Where-Object { $_ -eq 'CHANGELOG.md' }
if ($tocoCodigo -and -not $tocoChangelog) {
  Note "tocaste fantasma/ sin actualizar CHANGELOG.md - anotalo en [Unreleased]."
  Write-Host "    Checklist: hubo decision? -> ADR (docs/decisions). cambio el plan/alcance? -> ROADMAP.md."
}
else { Ok "CHANGELOG al dia (o sin cambios de codigo)" }

# 5. Doc-gate: blast-radius (CONTRIBUTING seccion 8, reglas mecanicas) -------
Write-Host "`n-- Doc-gate (blast-radius seccion 8) --"
$tocoCore     = $changed | Where-Object { $_ -like 'fantasma/core/*' }
$tocoFormato  = $changed | Where-Object { $_ -eq 'docs/formato-datos.md' }
$tocoViz      = $changed | Where-Object { $_ -like 'fantasma/viz/*' }
$tocoHud      = $changed | Where-Object { $_ -eq 'docs/hud-reference.md' }
$tocoUi       = $changed | Where-Object { $_ -like 'fantasma/ui/*' }
$tocoGuia     = $changed | Where-Object { $_ -eq 'docs/guia-usuario.md' }
$tocoBarreras = $changed | Where-Object { $_ -like '.githooks/*' -or $_ -like '.claude/hooks/*' -or $_ -eq '.claude/settings.json' -or $_ -eq 'tools/verificar.ps1' -or $_ -like '.github/workflows/*' }
$tocoFlujo    = $changed | Where-Object { $_ -eq 'docs/flujo-de-trabajo.md' }
$faltaFormato = $tocoCore     -and -not $tocoFormato
$faltaHud     = $tocoViz      -and -not $tocoHud
$faltaGuia    = $tocoUi       -and -not $tocoGuia
$faltaFlujo   = $tocoBarreras -and -not $tocoFlujo
if ($faltaFormato) { Block "tocaste fantasma/core/ sin docs/formato-datos.md (algoritmo/JSON/CSV). Ver CONTRIBUTING.md seccion 8 -> pasalo al escribano." }
if ($faltaHud)     { Block "tocaste fantasma/viz/ (HUD/overlay) sin docs/hud-reference.md. Ver CONTRIBUTING.md seccion 8 -> pasalo al escribano." }
if ($faltaGuia)    { Block "tocaste fantasma/ui/ sin docs/guia-usuario.md (UX/layout). Ver CONTRIBUTING.md seccion 8 -> pasalo al escribano." }
if ($faltaFlujo)   { Block "tocaste las barreras (hooks/gate/CI) sin docs/flujo-de-trabajo.md. Ver CONTRIBUTING.md seccion 8 -> pasalo al escribano." }
if (-not ($faltaFormato -or $faltaHud -or $faltaGuia -or $faltaFlujo)) { Ok "docs duenos al dia (o sin cambios en core/viz/ui/barreras)" }

# 6. Doc-gate: integridad del grafo de docs (product/ + engineering/) --------
# Lo corre el auditor determinista (auditar.ps1): frontmatter, wikilinks rotos,
# criterios de capacidades vigentes, huerfanos. BLOQUEA igual que el doc-drift de
# la seccion 8 (mismo principio: determinismo bloquea). Ver ADR 0016.
Write-Host "`n-- Doc-gate (grafo product/engineering: auditar.ps1) --"
& "$PSScriptRoot/auditar.ps1" -Bloquea | Out-Host
if ($LASTEXITCODE -eq 0) { Ok "grafo de docs integro (o solo avisos)" }
else { Block "el auditor del grafo encontro hallazgos BLOQUEA (arriba). Ver tools/auditar.ps1 y ADR 0016." }

# Resumen -------------------------------------------------------------------
Write-Host ""
if ($script:block -gt 0) {
  Write-Host "== $($script:block) bloqueo(s) de doc-drift (seccion 8). PUSH DETENIDO. ==" -ForegroundColor Red
  Write-Host "   Sincroniza los docs duenos (pasalo al escribano) y reintenta, o 'git push --no-verify' a proposito." -ForegroundColor Red
  if ($script:warn -gt 0) { Write-Host "   (+$($script:warn) aviso[s] no bloqueante[s] arriba.)" -ForegroundColor Yellow }
  exit 1
}
elseif ($script:warn -gt 0) {
  Write-Host "== $($script:warn) aviso(s) no bloqueante(s). El CI hara cumplir lint/formato/tests. ==" -ForegroundColor Yellow
  exit 0
}
else { Write-Host "== Todo limpio. ==" -ForegroundColor Green; exit 0 }
