# gemba-stop.ps1 - Stop hook (Gemba: ir a ver el demo). Si hay cambios sin
# commitear en areas VISUALES, exige EVIDENCIA VERIFICABLE en qa_runs/ antes de
# cerrar: un veredicto de QA visual sin artefacto no vale (disparo
# evidencia-no-palabra). El gate lee el artefacto, no la palabra del agente.
#
# Cosechado de los labs (criterio-no-copia, ADR 0007): alla el rol se llamaba por
# nombre propio y las rutas eran del proyecto; aqui es generico. SE AUTO-CONFIGURA
# desde tools/blast-radius.json: dispara si el diff toca 'fuente' de areas con
# rol 'revisor-visual'. Si ninguna area lo es, el hook esta DORMIDO (exit limpio;
# su dormancia se declara en andon/README.md, no se re-anuncia cada turno).
#
# EVIDENCIA FRESCA = algun archivo bajo qa_runs/ mas reciente que el ultimo cambio
# visual (mtime; corre local en Stop, donde el mtime es fiable). Respaldo anti-bucle:
# marcador .claude/.gemba-marker (gitignored) con el SHA1 del diff ya aprobado por
# el cliente -- valvula HUMANA para el caso raro de aprobar sin artefacto, NO
# auto-firma del agente. Archivo ASCII a proposito.
#
# ERRORES (ALTO-04): sin $ErrorActionPreference global; cada git real revisa
# $LASTEXITCODE y AVISA (sin block) si git falla de verdad. "No es repo git" sigue
# siendo salida limpia a proposito.

# Evitar bucle si este stop ya viene de un stop-hook.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }
$repo = (git rev-parse --show-toplevel 2>$null)
if (-not $repo) { exit 0 }

function Write-GitFailWarning($comando, $detalle) {
  $ctx = "AVISO (gemba-stop): '$comando' fallo (exit $LASTEXITCODE): $detalle. " +
         "No se pudo comprobar cambios visuales; revisalos a mano y deja evidencia en qa_runs/ si aplica."
  $out = @{ hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx } }
  $out | ConvertTo-Json -Compress -Depth 5
}

# Areas visuales del manifiesto (rol revisor-visual). Se auto-configura.
$manifestPath = Join-Path $repo 'tools/blast-radius.json'
if (-not (Test-Path $manifestPath)) { exit 0 }
try { $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json } catch { exit 0 }
$areasVis = @($manifest | Where-Object { $_.rol -eq 'revisor-visual' })
if ($areasVis.Count -eq 0) { exit 0 }   # dormido: no hay areas visuales

function Test-Pattern($path, $pattern) {
  if ($pattern -notlike '*/*' -and $path -like '*/*') { return $false }
  return ($path -like $pattern)
}

# Cambios visuales sin commitear.
$statusRaw = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) { Write-GitFailWarning 'git status --porcelain' ($statusRaw -join ' '); exit 0 }
$changed = @($statusRaw) | ForEach-Object { $s = "$_"; if ($s.Length -gt 3) { $s.Substring(3).Trim() } }
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
# Evidencia fresca Y RASTREADA POR GIT: la evidencia citada debe estar en el indice
# (git add -f; qa_runs/ suele estar gitignoreado), no solo en disco. Un archivo que
# nunca se commitea satisface el mtime pero no vale -- evidencia-no-palabra exige que
# EXISTA EN GIT, no solo en disco (leccion de campo, cosecha del lazo: un gate que mira
# el working tree se satisface con evidencia que git nunca vera). Solo cuentan los
# archivos de qa_runs/ que git rastrea.
# core.quotepath=false: que git NO cite/octalice rutas no-ASCII (asi Test-Path las halla).
$qaTrackedRaw = git -C $repo -c core.quotepath=false ls-files -- qa_runs 2>&1
if ($LASTEXITCODE -ne 0) { Write-GitFailWarning 'git ls-files -- qa_runs' ($qaTrackedRaw -join ' '); exit 0 }
foreach ($rel in @($qaTrackedRaw)) {
  if (-not $rel) { continue }
  $abs = Join-Path $repo $rel
  if ((Test-Path -LiteralPath $abs) -and ((Get-Item -LiteralPath $abs).LastWriteTime -gt $lastVis)) {
    exit 0   # artefacto de QA rastreado por git y posterior al cambio: evidencia valida
  }
}

# Respaldo anti-bucle: este diff exacto ya fue aprobado por el cliente sin artefacto.
$diffRaw = git diff HEAD -- $visChanged 2>&1
if ($LASTEXITCODE -ne 0) { Write-GitFailWarning 'git diff HEAD -- <visuales>' ($diffRaw -join ' '); exit 0 }
$payload = (($diffRaw) -join "`n") + "|" + ($visChanged -join "`n")
$sha1 = New-Object System.Security.Cryptography.SHA1Managed
$sha = [System.BitConverter]::ToString($sha1.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))).Replace('-','')
$marker = Join-Path $repo '.claude\.gemba-marker'
$last = if (Test-Path $marker) { (Get-Content $marker -Raw).Trim() } else { '' }
if ($sha -eq $last) { exit 0 }

$fecha = Get-Date -Format 'yyyyMMdd-HHmmss'
$ctx = "Gemba (revisor-visual): tocaste areas visuales (" + (($visChanged | Select-Object -First 5) -join ', ') + ") " +
       "y NO hay evidencia en qa_runs/ posterior al cambio. Un veredicto de QA sin artefacto no vale (evidencia-no-palabra). " +
       "QUE HACER: [1] corre la UI o el render DE VERDAD con casos de uso reales (datos sinteticos), no 'renderiza sin excepcion'; " +
       "[2] guarda la evidencia (capturas, logs de la corrida) en qa_runs/gemba-$fecha/ y FORZALA al indice con 'git add -f qa_runs/gemba-$fecha/...' -- qa_runs/ esta gitignoreado, y solo cuenta la evidencia que git rastrea (no basta dejarla en disco); " +
       "[3] presenta las capturas al cliente -- Gemba es checkpoint que vuelve al cliente, no juzga solo. " +
       "Caso raro (el cliente aprueba sin artefacto): Set-Content -Encoding ASCII '.claude/.gemba-marker' '$sha'"
$out = @{
  decision = 'block'
  reason   = 'Cambio visual sin evidencia de QA en qa_runs/ (gemba-stop).'
  hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
