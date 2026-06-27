# escribano-stop.ps1 - Stop hook. Si al cerrar hay doc-drift de la seccion 8
# (core/ sin formato-datos, viz/ sin hud-reference), frena el cierre y manda a
# Claude a correr el skill 'escribano'. Cuando los docs quedan sincronizados ya
# no bloquea -> el bucle se termina solo. Archivo ASCII (sin acentos) a proposito.

$ErrorActionPreference = 'SilentlyContinue'

# 1. Leer el input del hook. Si este stop YA viene de un stop-hook, no re-bloquear
#    (evita bucles aunque el escribano no logre cerrar el drift).
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

# 2. Detectar drift seccion 8 sobre los cambios sin commitear.
if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }
$changed = (git status --porcelain) | ForEach-Object { if ($_.Length -gt 3) { $_.Substring(3) } }
$tocoCore    = $changed | Where-Object { $_ -like 'fantasma/core/*' }
$tocoFormato = $changed | Where-Object { $_ -eq 'docs/formato-datos.md' }
$tocoViz     = $changed | Where-Object { $_ -like 'fantasma/viz/*' }
$tocoHud     = $changed | Where-Object { $_ -eq 'docs/hud-reference.md' }
$tocoUi      = $changed | Where-Object { $_ -like 'fantasma/ui/*' }
$tocoGuia    = $changed | Where-Object { $_ -eq 'docs/guia-usuario.md' }
$tocoBarr    = $changed | Where-Object { $_ -like '.githooks/*' -or $_ -like '.claude/hooks/*' -or $_ -eq '.claude/settings.json' -or $_ -eq 'tools/verificar.ps1' -or $_ -like '.github/workflows/*' }
$tocoFlujo   = $changed | Where-Object { $_ -eq 'docs/flujo-de-trabajo.md' }
$faltas = @()
if ($tocoCore -and -not $tocoFormato) { $faltas += 'fantasma/core/ -> docs/formato-datos.md' }
if ($tocoViz  -and -not $tocoHud)     { $faltas += 'fantasma/viz/ -> docs/hud-reference.md' }
if ($tocoUi   -and -not $tocoGuia)    { $faltas += 'fantasma/ui/ -> docs/guia-usuario.md' }
if ($tocoBarr -and -not $tocoFlujo)   { $faltas += 'barreras (hooks/gate/CI) -> docs/flujo-de-trabajo.md' }

# 3. Sin drift: dejar cerrar. Con drift: bloquear y mandar al escribano.
if ($faltas.Count -eq 0) { exit 0 }

$ctx = "Doc-drift seccion 8: cambiaste codigo sin su doc dueno (" + ($faltas -join '; ') + "). " +
       "Invoca el skill 'escribano' AHORA para sincronizar los docs duenos antes de cerrar. " +
       "Si el cambio implica una DECISION (no solo un cambio), no la escribas: senala que falta un ADR."
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
