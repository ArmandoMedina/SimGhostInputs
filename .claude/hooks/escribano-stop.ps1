# escribano-stop.ps1 - Stop hook. Si al cerrar hay doc-drift (segun blast-radius.json,
# seccion 8 de CONTRIBUTING), frena el cierre y manda al Escribano a sincronizar.
# Cuando todos los docs duenos estan sincronizados, el hook deja cerrar solo.
# Archivo ASCII (sin acentos) a proposito.
#
# VENTANA: este hook evalua git status --porcelain (cambios SIN commitear).
# El gate de push (verificar.ps1) evalua @{u}..HEAD (commiteado sin pushear).
# Si committeas sin docs, esta ventana ya no detecta el drift -> el gate lo atrapa.
# Para nada se pierda: commitea docs y codigo juntos, o usa el gate antes de pushear.

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

# 3. Leer el manifiesto unico de blast-radius.
$manifestPath = Join-Path $repo 'tools/blast-radius.json'
if (-not (Test-Path $manifestPath)) { exit 0 }
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

function Match-Any($list, $pattern) {
  foreach ($item in $list) { if ($item -like $pattern) { return $true } }
  return $false
}

# 4. Detectar drift: doc_bloquea faltantes (los AVISA no bloquean el hook).
$faltas = @()
foreach ($entry in $manifest) {
  $areaMatch = $false
  foreach ($pat in $entry.fuente) {
    if (Match-Any $changed $pat) { $areaMatch = $true; break }
  }
  if (-not $areaMatch) { continue }

  foreach ($tgt in $entry.doc_bloquea) {
    if (-not (Match-Any $changed $tgt)) {
      $faltas += "$($entry.fuente -join '/') -> $tgt (rol: $($entry.rol))"
    }
  }
}

# 5. Sin drift en doc_bloquea: dejar cerrar. Con drift: bloquear y mandar al Escribano.
if ($faltas.Count -eq 0) { exit 0 }

$ctx = "Doc-drift seccion 8 (blast-radius.json): cambiaste codigo sin su doc dueno. " +
       "Faltas: " + ($faltas -join '; ') + ". " +
       "Invoca el skill 'escribano' AHORA para sincronizar los docs duenos antes de cerrar. " +
       "Si el cambio implica una DECISION (no solo un cambio de codigo), no la escribas: senala que falta un ADR. " +
       "NOTA: este hook ve cambios sin commitear (working tree). Si ya committeaste sin los docs, " +
       "el drift lo atrapa verificar.ps1 al hacer push."
$out = @{
  decision = 'block'
  reason   = 'Faltan docs duenos (seccion 8). Corriendo el escribano antes de cerrar.'
  hookSpecificOutput = @{
    hookEventName     = 'Stop'
    additionalContext = $ctx
  }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
