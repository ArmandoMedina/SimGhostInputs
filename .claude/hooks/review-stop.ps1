# review-stop.ps1 - Stop hook. Si hay codigo nuevo en fantasma/ sin revisar,
# frena el cierre y manda a correr /code-review. Usa un marcador con el hash del
# diff ya revisado (.claude/.review-marker, gitignored) para no re-revisar lo
# mismo: igual que el escribano, se termina solo. Archivo ASCII a proposito.
#
# ERRORES (ALTO-04, fase3-hooks.md): sin $ErrorActionPreference global. Las llamadas
# reales a git (status/diff) se revisan por $LASTEXITCODE; si git falla de verdad
# (no "sin cambios que revisar" sino un fallo real: git no disponible, repo corrupto,
# permisos), el hook AVISA (additionalContext, sin decision=block: sigue sin bloquear)
# en vez de tratarlo en silencio como "nada que revisar".

# Evitar bucle si este stop ya viene de un stop-hook.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }

function Write-GitFailWarning($comando, $detalle) {
  $ctx = "AVISO (review-stop): '$comando' fallo (exit $LASTEXITCODE): $detalle. " +
         "No se pudo comprobar si hay codigo sin revisar en fantasma/; revisalo a mano " +
         "con /code-review antes de cerrar."
  $out = @{ hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx } }
  $out | ConvertTo-Json -Compress -Depth 5
}

# Hay codigo sin commitear en fantasma/?
$statusRaw = git status --porcelain -- fantasma 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-GitFailWarning 'git status --porcelain -- fantasma' ($statusRaw -join ' ')
  exit 0
}
$codeChanged = $statusRaw | Where-Object { $_ }
if (-not $codeChanged) { exit 0 }

# Hash del estado revisable actual (cambios rastreados + lista de no rastreados).
$diffRaw = git diff HEAD -- fantasma 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-GitFailWarning 'git diff HEAD -- fantasma' ($diffRaw -join ' ')
  exit 0
}
$payload = (($diffRaw) -join "`n") + "|" + (($codeChanged) -join "`n")
$sha1 = New-Object System.Security.Cryptography.SHA1Managed
$sha = [System.BitConverter]::ToString($sha1.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))).Replace('-','')

$marker = Join-Path (Get-Location) ".claude\.review-marker"
$last = if (Test-Path $marker) { (Get-Content $marker -Raw).Trim() } else { '' }
if ($sha -eq $last) { exit 0 }   # este diff exacto ya se reviso

$ctx = "Hay codigo en fantasma/ sin revisar. Corre /code-review sobre el diff actual ANTES de cerrar (y antes del escribano). " +
       "Al terminar la revision y atender o anotar los hallazgos, marca este diff como revisado ejecutando exactamente: " +
       "Set-Content -Encoding ASCII '.claude/.review-marker' '$sha'"
$out = @{
  decision = 'block'
  reason   = 'Codigo sin revisar (Reviewer). Corriendo /code-review antes de cerrar.'
  hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
