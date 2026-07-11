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

param(
  [string]$Base = '',
  [string]$Manifiesto = '',
  [string]$Repo = ''
)

if (-not $Repo) { $Repo = Split-Path -Parent $PSScriptRoot }
Set-Location $Repo
$script:warn = 0
$script:block = 0

function Note($msg)  { Write-Host "  [AVISO] $msg"   -ForegroundColor Yellow; $script:warn++ }
function Block($msg) { Write-Host "  [BLOQUEA] $msg" -ForegroundColor Red;    $script:block++ }
function Ok($msg)    { Write-Host "  [OK] $msg"      -ForegroundColor Green }
function Fail($msg) {
  # Falla CERRADO (convergencia con Jidoka): si el gate no puede medir, NO aprueba (exit 2).
  Write-Host "  [ERROR] $msg" -ForegroundColor Red
  Write-Host ""
  Write-Host "== Gate sin veredicto: FALLA CERRADO (exit 2). ==" -ForegroundColor Red
  exit 2
}

# Matcher del manifiesto (homologado a starter v0.5.0, ADR 0019):
# un patron SIN '/' solo casa archivos en la raiz del repo.
function Test-Pattern($path, $pattern) {
  if ($pattern -notlike '*/*' -and $path -like '*/*') { return $false }
  return ($path -like $pattern)
}
# Devuelve $true si algun elemento de $list hace Test-Pattern con $pattern.
function Match-Any($list, $pattern) {
  foreach ($item in $list) { if (Test-Pattern $item $pattern) { return $true } }
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
if ($Base) { $changedCov = git diff --name-only "$Base...HEAD" 2>$null }
else {
  $upstreamCov = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
  if ($LASTEXITCODE -eq 0) { $changedCov = git diff --name-only '@{u}..HEAD' }
  else { $changedCov = git diff --name-only HEAD }
}
$tocoCodigoCov = $changedCov | Where-Object { $_ -like 'fantasma/*' }
$tocoTests     = $changedCov | Where-Object { $_ -like 'tests/*' }
if ($tocoCodigoCov -and -not $tocoTests) {
  Note "tocaste fantasma/ sin cambios en tests/. Revisa si el cambio introduce comportamiento nuevo o modifica uno existente que no este cubierto aun."
  Write-Host "    Pistas: nueva funcion -> nuevo test; comportamiento cambiado -> test actualizado; refactor puro -> tests existentes ya cubren."
}
else { Ok "tests acompanan los cambios de codigo (o sin cambios en fantasma/)" }

# 5-a. Doc-gate: codigo tocado sin CHANGELOG ----------------------------------
Write-Host "`n-- Doc-gate (CHANGELOG) --"
if ($Base) {
  $changed = git diff --name-only "$Base...HEAD" 2>$null
  if ($LASTEXITCODE -ne 0) { Fail "no pude calcular el rango $Base...HEAD (base inexistente o historia incompleta)" }
}
else {
  $upstream = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
  if ($LASTEXITCODE -eq 0) {
    $changed = git diff --name-only '@{u}..HEAD' 2>$null
    if ($LASTEXITCODE -ne 0) { Fail "no pude calcular el rango @{u}..HEAD" }
  }
  else {
    $changed = git diff --name-only HEAD 2>$null
    if ($LASTEXITCODE -ne 0) { Fail "no pude leer el working tree (git diff HEAD)" }
  }
}
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
if (-not $Manifiesto) { $Manifiesto = "$PSScriptRoot/blast-radius.json" }
if (-not (Test-Path $Manifiesto)) { Fail "no encuentro la ley ($Manifiesto)" }
$manifest = Get-Content $Manifiesto -Raw | ConvertFrom-Json
if (-not $manifest) { Fail "la ley ($Manifiesto) no parsea como JSON" }
$hayBlastFalta = $false
$hayBlastAviso = $false

foreach ($entry in $manifest) {
  # Chequear si el area fue tocada (respetando 'excluye').
  $tocados = @()
  foreach ($f in $changed) {
    $enFuente = $false
    foreach ($pat in $entry.fuente) { if (Test-Pattern $f $pat) { $enFuente = $true; break } }
    if ($enFuente -and $entry.excluye) {
      foreach ($ex in $entry.excluye) { if (Test-Pattern $f $ex) { $enFuente = $false; break } }
    }
    if ($enFuente) { $tocados += $f }
  }
  if ($tocados.Count -eq 0) { continue }
  $quienes = ($tocados | Select-Object -First 3) -join ', '

  # docs_bloquea: BLOQUEA si falta alguno.
  foreach ($tgt in $entry.doc_bloquea) {
    if (-not (Match-Any $changed $tgt)) {
      Block "[$($entry.nombre)] tocaste $quienes sin $tgt ($($entry.desc)). Rol: $($entry.rol) -> pasalo al escribano."
      $hayBlastFalta = $true
    }
  }

  # doc_avisa: AVISA si falta alguno. El aviso local se asume bypaseable:
  # auditar-radius.ps1 lo re-verifica en el CI (rango del PR).
  foreach ($tgt in $entry.doc_avisa) {
    if (-not (Match-Any $changed $tgt)) {
      $extra = ""; if ($entry.mensaje) { $extra = " $($entry.mensaje)." }
      Note "[$($entry.nombre)] considera actualizar $tgt ($($entry.desc)). Rol: $($entry.rol).$extra El CI re-verifica esto."
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
