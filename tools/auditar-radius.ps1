#Requires -Version 5
# auditar-radius.ps1 - Auditoria DETERMINISTA del blast-radius (seccion 8 de
# CONTRIBUTING) sobre un rango de commits. Complementa a auditar.ps1 (que audita
# la INTEGRIDAD del grafo product/+engineering/): este audita que ningun commit
# haya tocado un area sin tocar su doc dueno. Cierra el hueco real de "PR verde
# con docs desfasadas": el hook de sesion solo ve el working tree y verificar.ps1
# solo corre al push local; este corre en CI sobre el rango del PR y no se salta.
# Homologado del starter v0.5.0 (ADR 0019).
#
# LA LEY vive en tools/blast-radius.json: este auditor NO trae reglas propias.
# Matcher: comodines -like; patron SIN '/' solo casa la raiz; 'excluye' resta;
# 'mensaje' se anexa al aviso. Manifiesto roto = BLOQUEA (ley rota no es ley
# apagada); sin manifiesto = gate apagado con aviso.
#
#   ./tools/auditar-radius.ps1                          # lo NO commiteado (vs HEAD)
#   ./tools/auditar-radius.ps1 -Range "master..HEAD"    # una rama / PR completa
#   ./tools/auditar-radius.ps1 -Range "HEAD~5..HEAD" -PorCommit
#
# Sale 1 si hay violacion doc_bloquea. Para que sea MURO: marcalo required check
# en branch protection (un job rojo no-requerido deja pasar el merge igual).
# ASCII a proposito (PS 5.1).

param([string]$Range = "", [switch]$PorCommit)

$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $PSScriptRoot)

$manifestPath = 'tools/blast-radius.json'
if (-not (Test-Path $manifestPath)) {
  Write-Host "[AVISO] sin tools/blast-radius.json: doc-gate apagado." -ForegroundColor Yellow
  exit 0
}
try { $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json }
catch {
  Write-Host "[BLOQUEA] tools/blast-radius.json no parsea como JSON. La ley rota bloquea: arreglala." -ForegroundColor Red
  exit 1
}

function Test-Pattern($path, $pattern) {
  if ($pattern -notlike '*/*' -and $path -like '*/*') { return $false }
  return ($path -like $pattern)
}
function Match-Any($paths, $pattern) {
  foreach ($p in $paths) { if (Test-Pattern $p $pattern) { return $true } }
  return $false
}

function Get-Changed($rango) {
  if ($rango) { return @(git diff --name-only $rango) | Where-Object { $_ } }
  $c = @(); $c += git diff --name-only HEAD; $c += git diff --name-only --cached
  $c += git ls-files --others --exclude-standard
  return @($c | Where-Object { $_ } | Sort-Object -Unique)
}

function Audita($changed, $etiqueta) {
  $block = 0; $warn = 0
  Write-Host "-- $etiqueta ($($changed.Count) archivo[s]) --"
  foreach ($entry in $manifest) {
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
    $files = ($tocados | Select-Object -First 3) -join ', '

    foreach ($tgt in $entry.doc_bloquea) {
      if (Match-Any $changed $tgt) { Write-Host "  [OK] area '$($entry.nombre)' con su dueno '$tgt'" -ForegroundColor Green }
      else { Write-Host "  [BLOQUEA] area '$($entry.nombre)': {$files} sin su dueno '$tgt'. Rol: $($entry.rol) -> pasalo al escribano." -ForegroundColor Red; $block++ }
    }
    foreach ($tgt in @($entry.doc_avisa) + @($entry.product_avisa)) {
      if (-not $tgt) { continue }
      if (-not (Match-Any $changed $tgt)) {
        $extra = ""; if ($entry.mensaje) { $extra = " $($entry.mensaje)." }
        Write-Host "  [AVISA] area '$($entry.nombre)': {$files} sin tocar '$tgt' (rol $($entry.rol)).$extra" -ForegroundColor Yellow; $warn++
      }
    }
  }
  if (($block + $warn) -eq 0) { Write-Host "  [OK] sin areas gateadas tocadas o todo con dueno" -ForegroundColor Green }
  return @{ block = $block; warn = $warn }
}

Write-Host "== Auditoria blast-radius (seccion 8) =="
$totBlock = 0; $totWarn = 0
if ($PorCommit -and $Range) {
  foreach ($sha in @(git rev-list --reverse $Range)) {
    $res = Audita @(git diff-tree --no-commit-id --name-only -r $sha) (git log -1 --format='%h %s' $sha)
    $totBlock += $res.block; $totWarn += $res.warn
  }
} else {
  $etq = if ($Range) { "rango $Range" } else { "cambios sin commitear (vs HEAD)" }
  $res = Audita (Get-Changed $Range) $etq
  $totBlock = $res.block; $totWarn = $res.warn
}

Write-Host ""
if ($totBlock -gt 0) {
  Write-Host "== AUDITORIA FALLIDA: $totBlock que BLOQUEAN, $totWarn aviso(s). Sincroniza y re-audita. ==" -ForegroundColor Red
  exit 1
} elseif ($totWarn -gt 0) {
  Write-Host "== AUDITORIA con $totWarn aviso(s) (ninguno bloquea). ==" -ForegroundColor Yellow; exit 0
} else {
  Write-Host "== AUDITORIA LIMPIA: todos los flujos respetaron el blast-radius. ==" -ForegroundColor Green; exit 0
}
