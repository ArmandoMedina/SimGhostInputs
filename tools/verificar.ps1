#Requires -Version 5
# verificar.ps1 - Pipeline de barreras deterministas en MODO AVISO (no bloquea).
# Inspirado en el patron "no-mistakes" y en el hook de livotransfer. Se corre ANTES
# de subir: lint (ruff) + formato (ruff format) + tests (pytest) + doc-gate (CHANGELOG).
# El CI es la compuerta que SI bloquea; esto es la alarma temprana local.
#
# Uso:  ./tools/verificar.ps1
#
# Nota: archivo ASCII a proposito (sin acentos) para no depender del BOM en PS 5.1.

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$script:warn = 0

function Note($msg) { Write-Host "  [AVISO] $msg" -ForegroundColor Yellow; $script:warn++ }
function Ok($msg)   { Write-Host "  [OK] $msg"    -ForegroundColor Green }

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

# Resumen -------------------------------------------------------------------
Write-Host ""
if ($script:warn -gt 0) {
  Write-Host "== $($script:warn) aviso(s). El commit/push NO se bloquea (el CI si lo hara). ==" -ForegroundColor Yellow
}
else { Write-Host "== Todo limpio. ==" -ForegroundColor Green }
exit 0
