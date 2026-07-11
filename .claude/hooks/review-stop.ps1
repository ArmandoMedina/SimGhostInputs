# review-stop.ps1 - Stop hook. Si hay codigo sin revisar en el rango de cierre,
# frena y manda a correr /code-review. Cosechado de los labs (criterio-no-copia,
# ADR 0007): en el origen el area de codigo estaba hardcodeada a una carpeta fija; aqui se
# LEE de la ley (tools/blast-radius.json) -- las areas con "revisa": true aportan
# sus 'fuente' globs. Si ninguna area lo pide, el hook se declara dormido.
# Usa un marcador con el SHA del diff ya revisado (.claude/.review-marker,
# gitignored) para no re-revisar lo mismo: se termina solo. NO es auto-firma: el
# humano lo pone tras revisar, y el hook verifica que el SHA sea el del diff real.
# Archivo ASCII a proposito (PS 5.1 sin BOM). Disparos: no-verify-es-teatro,
# prueba-de-vida-del-gate.
#
# ERRORES (ALTO-04): sin $ErrorActionPreference global. Cada git real revisa
# $LASTEXITCODE; si git falla de verdad (no "sin cambios" sino fallo real), el
# hook AVISA (additionalContext, sin decision=block) en vez de callar.

# Evitar bucle si este stop ya viene de un stop-hook.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }
$repo = (git rev-parse --show-toplevel 2>$null)
if (-not $repo) { exit 0 }

function Write-GitFailWarning($comando, $detalle) {
  $ctx = "AVISO (review-stop): '$comando' fallo (exit $LASTEXITCODE): $detalle. " +
         "No se pudo comprobar si hay codigo sin revisar; revisalo a mano con /code-review antes de cerrar."
  $out = @{ hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx } }
  $out | ConvertTo-Json -Compress -Depth 5
}

# Areas de codigo del manifiesto (las que piden "revisa": true). Se auto-configura.
$manifestPath = Join-Path $repo 'tools/blast-radius.json'
if (-not (Test-Path $manifestPath)) { exit 0 }
try { $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json } catch { exit 0 }
$areasCod = @($manifest | Where-Object { $_.revisa -eq $true })
if ($areasCod.Count -eq 0) { exit 0 }   # dormido: ninguna area pide revision

function Test-Pattern($path, $pattern) {
  if ($pattern -notlike '*/*' -and $path -like '*/*') { return $false }
  return ($path -like $pattern)
}

# Codigo sin commitear que caiga en un area de revision.
$statusRaw = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) { Write-GitFailWarning 'git status --porcelain' ($statusRaw -join ' '); exit 0 }
$changed = @($statusRaw) | ForEach-Object { $s = "$_"; if ($s.Length -gt 3) { $s.Substring(3).Trim() } }
$codChanged = @()
foreach ($f in $changed) {
  foreach ($area in $areasCod) {
    $hit = $false
    foreach ($pat in $area.fuente) { if (Test-Pattern $f $pat) { $hit = $true; break } }
    if ($hit -and $area.excluye) {
      foreach ($ex in $area.excluye) { if (Test-Pattern $f $ex) { $hit = $false; break } }
    }
    if ($hit) { $codChanged += $f; break }
  }
}
if ($codChanged.Count -eq 0) { exit 0 }

# SHA del estado revisable actual (diff + lista de archivos).
$diffRaw = git diff HEAD -- $codChanged 2>&1
if ($LASTEXITCODE -ne 0) { Write-GitFailWarning 'git diff HEAD -- <codigo>' ($diffRaw -join ' '); exit 0 }
$payload = (($diffRaw) -join "`n") + "|" + (($codChanged) -join "`n")
$sha1 = New-Object System.Security.Cryptography.SHA1Managed
$sha = [System.BitConverter]::ToString($sha1.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))).Replace('-','')

$marker = Join-Path $repo '.claude\.review-marker'
$last = if (Test-Path $marker) { (Get-Content $marker -Raw).Trim() } else { '' }
if ($sha -eq $last) { exit 0 }   # este diff exacto ya se reviso

$ctx = "Hay codigo sin revisar (" + (($codChanged | Select-Object -First 5) -join ', ') + "). " +
       "Corre /code-review sobre el diff actual ANTES de cerrar (y antes del escribano). " +
       "No uses --no-verify ni maquilles el estado staged para pasar (disparo no-verify-es-teatro): " +
       "el muro real es el required check server-side. Al terminar la revision y atender o anotar los " +
       "hallazgos, marca este diff como revisado ejecutando exactamente: " +
       "Set-Content -Encoding ASCII '.claude/.review-marker' '$sha'"
$out = @{
  decision = 'block'
  reason   = 'Codigo sin revisar. Corre /code-review sobre el diff antes de cerrar.'
  hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
