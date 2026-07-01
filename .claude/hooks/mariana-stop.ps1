# mariana-stop.ps1 - Stop hook (rol Mariana, UX visual). Si hay cambios sin
# commitear en areas visuales, exige EVIDENCIA VERIFICABLE en qa_runs/ antes de
# dar por terminado (homologado del starter v0.5.0, ADR 0019): un veredicto de
# QA visual sin artefacto (screenshot, log de corrida) no vale - las pruebas
# "clic por clic" que solo se afirman ya fallaron aqui. El gate lee el
# artefacto, no la palabra del agente.
#
# SE AUTO-CONFIGURA desde tools/blast-radius.json: dispara si el diff toca
# 'fuente' de areas con rol 'Mariana'. Mariana NO detecta sola si algo se ve
# mal (limite semantico: eso es juicio del PO); obliga a mirar Y a dejar rastro.
#
# EVIDENCIA FRESCA = algun archivo bajo qa_runs/ mas reciente que el ultimo
# cambio visual. Respaldo anti-bucle: marcador .claude/.mariana-marker
# (gitignored) con el SHA1 del diff ya aprobado por el PO - solo para el caso
# raro de aprobar sin artefacto. Ver ADR 0011 (cableado) y ADR 0019 (evidencia).
# Archivo ASCII (sin acentos) a proposito.

$ErrorActionPreference = 'SilentlyContinue'

# Evitar bucle si este stop ya viene de un stop-hook.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }
$repo = (git rev-parse --show-toplevel 2>$null)
if (-not $repo) { exit 0 }

# Areas visuales del manifiesto (rol Mariana).
$manifestPath = Join-Path $repo 'tools/blast-radius.json'
if (-not (Test-Path $manifestPath)) { exit 0 }
try { $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json } catch { exit 0 }
$areasVis = @($manifest | Where-Object { $_.rol -eq 'Mariana' })
if ($areasVis.Count -eq 0) { exit 0 }

function Test-Pattern($path, $pattern) {
  if ($pattern -notlike '*/*' -and $path -like '*/*') { return $false }
  return ($path -like $pattern)
}

# Cambios visuales sin commitear.
$changed = (git status --porcelain) | ForEach-Object { if ($_.Length -gt 3) { $_.Substring(3).Trim() } }
$visChanged = @()
foreach ($f in $changed) {
  foreach ($area in $areasVis) {
    $hit = $false
    foreach ($pat in $area.fuente) { if (Test-Pattern $f $pat) { $hit = $true; break } }
    if ($hit -and $area.excluye) {
      foreach ($ex in $area.excluye) { if (Test-Pattern $f $ex) { $hit = $false; break } }
    }
    if ($hit) { $visChanged += $f; break }
  }
}
if ($visChanged.Count -eq 0) { exit 0 }

# Evidencia fresca: algo en qa_runs/ mas nuevo que el ultimo cambio visual.
$lastVis = Get-Date '2000-01-01'
foreach ($f in $visChanged) {
  $p = Join-Path $repo $f
  if (Test-Path -LiteralPath $p) {
    $t = (Get-Item -LiteralPath $p).LastWriteTime
    if ($t -gt $lastVis) { $lastVis = $t }
  }
}
$qaDir = Join-Path $repo 'qa_runs'
if (Test-Path $qaDir) {
  $fresh = Get-ChildItem $qaDir -Recurse -File | Where-Object { $_.LastWriteTime -gt $lastVis } | Select-Object -First 1
  if ($fresh) { exit 0 }   # hay artefacto de QA posterior al cambio: evidencia valida
}

# Respaldo anti-bucle: este diff exacto ya fue aprobado por el PO sin artefacto.
$payload = ((git diff HEAD -- $visChanged) -join "`n") + "|" + ($visChanged -join "`n")
$sha1 = New-Object System.Security.Cryptography.SHA1Managed
$sha = [System.BitConverter]::ToString($sha1.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))).Replace('-','')
$marker = Join-Path $repo '.claude\.mariana-marker'
$last = if (Test-Path $marker) { (Get-Content $marker -Raw).Trim() } else { '' }
if ($sha -eq $last) { exit 0 }

$fecha = Get-Date -Format 'yyyyMMdd-HHmmss'
$ctx = "Rol Mariana (UX visual): tocaste areas visuales (" + (($visChanged | Select-Object -First 5) -join ', ') + ") " +
       "y NO hay evidencia en qa_runs/ posterior al cambio. Un veredicto de QA sin artefacto no vale (ADR 0019). " +
       "QUE HACER: [1] corre la UI o el render DE VERDAD con casos de uso reales (fantasma-ng o el material " +
       "de docs/recursos-del-proyecto.md), no solo 'renderiza sin excepcion'; " +
       "[2] guarda la evidencia (screenshots, logs de la corrida) en qa_runs/mariana-$fecha/ " +
       "(convencion en qa_runs/README.md); " +
       "[3] completa la checklist de QA visual (docs/ux-patterns.md sec 2-B: heuristicas, coherencia, " +
       "HUD legible, vocabulario de pista, estados visibles); " +
       "[4] presenta las capturas al PO - Mariana es checkpoint que vuelve al PO, no juzga sola. " +
       "Caso raro (el PO aprueba sin artefacto): Set-Content -Encoding ASCII '.claude/.mariana-marker' '$sha'"
$out = @{
  decision = 'block'
  reason   = 'Cambio visual sin evidencia de QA en qa_runs/ (Mariana, ADR 0019).'
  hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
