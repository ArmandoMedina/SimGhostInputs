# escribano-stop.ps1 - Stop hook. Si al cerrar hay doc-drift (segun blast-radius.json,
# seccion 8 de CONTRIBUTING), frena el cierre y manda al Escribano a sincronizar.
# Cuando todos los docs duenos estan sincronizados, el hook deja cerrar solo.
# Archivo ASCII (sin acentos) a proposito.
#
# VENTANA: este hook evalua git status --porcelain (cambios SIN commitear).
# El gate de push (verificar.ps1) evalua @{u}..HEAD (commiteado sin pushear).
# Si committeas sin docs, esta ventana ya no detecta el drift: lo atrapan
# verificar.ps1 al push y auditar-radius.ps1 en CI (rango del PR).
#
# Matcher (homologado a starter v0.5.0, ADR 0019): comodines -like; un patron
# SIN '/' solo casa archivos en la raiz del repo; 'excluye' (opcional) resta
# rutas; 'mensaje' (opcional) se anexa al aviso.

$ErrorActionPreference = 'SilentlyContinue'

# 1. Leer el input del hook. Si este stop YA viene de un stop-hook, no re-bloquear.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

# 2. Obtener lista de archivos con cambios sin commitear.
if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }
$repo = (git rev-parse --show-toplevel 2>$null)
if (-not $repo) { exit 0 }
$changed = (git status --porcelain) | ForEach-Object { if ($_.Length -gt 3) { $_.Substring(3).Trim() } }
if (-not $changed) { exit 0 }

# 3. Leer el manifiesto unico de blast-radius (la ley).
$manifestPath = Join-Path $repo 'tools/blast-radius.json'
if (-not (Test-Path $manifestPath)) { exit 0 }
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

function Test-Pattern($path, $pattern) {
  # Patron sin '/' = solo raiz del repo (un '*.md' no debe casar docs/x.md).
  if ($pattern -notlike '*/*' -and $path -like '*/*') { return $false }
  return ($path -like $pattern)
}
function Match-Any($paths, $pattern) {
  foreach ($p in $paths) { if (Test-Pattern $p $pattern) { return $true } }
  return $false
}

# 4. Detectar drift: doc_bloquea faltantes bloquean; doc_avisa solo acompana
#    el mensaje (los avisos puros los cobran verificar.ps1 y el CI).
$faltas = @()
$avisos = @()
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

  foreach ($tgt in $entry.doc_bloquea) {
    if (-not (Match-Any $changed $tgt)) {
      $faltas += "area '$($entry.nombre)' (tocaste $(($tocados | Select-Object -First 3) -join ', ')): falta su doc dueno '$tgt' (rol $($entry.rol))"
    }
  }
  foreach ($tgt in @($entry.doc_avisa) + @($entry.product_avisa)) {
    if ($tgt -and -not (Match-Any $changed $tgt)) {
      $linea = "area '$($entry.nombre)': revisa '$tgt' (rol $($entry.rol))"
      if ($entry.mensaje) { $linea += " - $($entry.mensaje)" }
      $avisos += $linea
    }
  }
}

# 5. Sin drift en doc_bloquea: dejar cerrar. Con drift: bloquear y mandar al Escribano.
if ($faltas.Count -eq 0) { exit 0 }

$ctx = "Doc-drift seccion 8 (la ley: tools/blast-radius.json). BLOQUEA: " + ($faltas -join '; ') + ". "
if ($avisos.Count -gt 0) { $ctx += "AVISOS no bloqueantes (verificar y el CI los re-verifican): " + (($avisos | Select-Object -First 5) -join '; ') + ". " }
$ctx += "Invoca el skill 'escribano' AHORA para sincronizar los docs duenos antes de cerrar " +
        "(si eres el orquestador, delegalo: subagente general + .claude/skills/escribano/SKILL.md en el prompt). " +
        "Si el cambio implica una DECISION (no solo un cambio de codigo), no la escribas: senala que falta un ADR. " +
        "NOTA: este hook ve cambios sin commitear (working tree). Si ya committeaste sin los docs, " +
        "el drift lo atrapan verificar.ps1 al push y auditar-radius.ps1 en el CI."
$out = @{
  decision = 'block'
  reason   = 'Faltan docs duenos (seccion 8, blast-radius.json). Corre el escribano antes de cerrar.'
  hookSpecificOutput = @{
    hookEventName     = 'Stop'
    additionalContext = $ctx
  }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
