# review-stop.ps1 - Stop hook. Si hay codigo nuevo en fantasma/ sin revisar,
# frena el cierre y manda a correr /code-review. Usa un marcador con el hash del
# diff ya revisado (.claude/.review-marker, gitignored) para no re-revisar lo
# mismo: igual que el escribano, se termina solo. Archivo ASCII a proposito.

$ErrorActionPreference = 'SilentlyContinue'

# Evitar bucle si este stop ya viene de un stop-hook.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }

# Hay codigo sin commitear en fantasma/?
$codeChanged = (git status --porcelain -- fantasma) | Where-Object { $_ }
if (-not $codeChanged) { exit 0 }

# Hash del estado revisable actual (cambios rastreados + lista de no rastreados).
$payload = ((git diff HEAD -- fantasma) -join "`n") + "|" + (($codeChanged) -join "`n")
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
