#Requires -Version 5
# verificar.ps1 - Pipeline de barreras deterministas local. Se corre ANTES de subir:
# lint (ruff) + formato (ruff format) + tests (pytest) + doc-gate + auditor del grafo.
# Inspirado en el patron "no-mistakes" (convenciones de metodo: project-starter).
# lint/formato/tests AVISAN (el CI los hace cumplir); el doc-drift de la seccion 8
# (segun blast-radius.json) y los hallazgos BLOQUEA del auditor del grafo de docs
# (auditar.ps1: wikilinks rotos, frontmatter, criterios) BLOQUEAN el push (exit 1).
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

# Devuelve $true si algun elemento de $list hace -like $pattern.
function Match-Any($list, $pattern) {
  foreach ($item in $list) { if ($item -like $pattern) { return $true } }
  return $false
}

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

# 4. Cobertura de tests: codigo tocado sin tests ----------------------------
Write-Host "`n-- Cobertura de tests --"
$upstreamCov = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
if ($LASTEXITCODE -eq 0) { $changedCov = git diff --name-only '@{u}..HEAD' }
else { $changedCov = git diff --name-only HEAD }
$tocoCodigoCov = $changedCov | Where-Object { $_ -like 'fantasma/*' }
$tocoTests     = $changedCov | Where-Object { $_ -like 'tests/*' }
if ($tocoCodigoCov -and -not $tocoTests) {
  Note "tocaste fantasma/ sin cambios en tests/. Revisa si el cambio introduce comportamiento nuevo o modifica uno existente que no este cubierto aun."
  Write-Host "    Pistas: nueva funcion -> nuevo test; comportamiento cambiado -> test actualizado; refactor puro -> tests existentes ya cubren."
}
else { Ok "tests acompanan los cambios de codigo (o sin cambios en fantasma/)" }

# 5-a. Doc-gate: codigo tocado sin CHANGELOG ----------------------------------
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

# 5-b. Doc-gate: blast-radius (tools/blast-radius.json, CONTRIBUTING seccion 8) --
# Fuente unica de verdad ejecutable. Para agregar un area o un doc dueno: edita
# blast-radius.json y esto funciona sin mas cambios. Ver CONTRIBUTING.md seccion 8.
Write-Host "`n-- Doc-gate (blast-radius seccion 8) --"
$manifest = Get-Content "$PSScriptRoot/blast-radius.json" -Raw | ConvertFrom-Json
$hayBlastFalta = $false
$hayBlastAviso = $false

foreach ($entry in $manifest) {
  # Chequear si el area fue tocada.
  $areaMatch = $false
  foreach ($pat in $entry.fuente) {
    if (Match-Any $changed $pat) { $areaMatch = $true; break }
  }
  if (-not $areaMatch) { continue }

  # docs_bloquea: BLOQUEA si falta alguno.
  foreach ($tgt in $entry.doc_bloquea) {
    if (-not (Match-Any $changed $tgt)) {
      Block "[$($entry.nombre)] tocaste $($entry.fuente -join '/') sin $tgt ($($entry.desc)). Rol: $($entry.rol) -> pasalo al escribano."
      $hayBlastFalta = $true
    }
  }

  # doc_avisa: AVISA si falta alguno.
  foreach ($tgt in $entry.doc_avisa) {
    if (-not (Match-Any $changed $tgt)) {
      Note "[$($entry.nombre)] considera actualizar $tgt ($($entry.desc)). Rol: $($entry.rol)."
      $hayBlastAviso = $true
    }
  }

  # product_avisa: AVISA si ninguno de los patrones de product/ fue tocado.
  if ($entry.product_avisa.Count -gt 0) {
    $anyProduct = $false
    foreach ($pat in $entry.product_avisa) {
      if (Match-Any $changed $pat) { $anyProduct = $true; break }
    }
    if (-not $anyProduct) {
      Note "[$($entry.nombre)] preguntate: las capacidades/modulos de product/ siguen describiendo lo que implementaste? Candidatos: $($entry.product_avisa -join ', '). Escribano los sincroniza si cambiaron criterios."
      $hayBlastAviso = $true
    }
  }
}

if (-not $hayBlastFalta -and -not $hayBlastAviso) { Ok "blast-radius al dia (o sin cambios en areas cubiertas)" }
elseif (-not $hayBlastFalta) { Write-Host "  (avisos arriba; nada que BLOQUEA en blast-radius)" -ForegroundColor Yellow }

# 5-c. Doc-gate: integridad del grafo de docs (product/ + engineering/) --------
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
  Write-Host "== $($script:block) bloqueo(s) de doc-drift. PUSH DETENIDO. ==" -ForegroundColor Red
  Write-Host "   Sincroniza los docs duenos (pasalo al escribano) y reintenta, o 'git push --no-verify' a proposito." -ForegroundColor Red
  if ($script:warn -gt 0) { Write-Host "   (+$($script:warn) aviso[s] no bloqueante[s] arriba.)" -ForegroundColor Yellow }
  exit 1
}
elseif ($script:warn -gt 0) {
  Write-Host "== $($script:warn) aviso(s) no bloqueante(s). El CI hara cumplir lint/formato/tests. ==" -ForegroundColor Yellow
  exit 0
}
else { Write-Host "== Todo limpio. ==" -ForegroundColor Green; exit 0 }
