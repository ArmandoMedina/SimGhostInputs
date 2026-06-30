# mariana-stop.ps1 - Stop hook (rol Mariana, UX visual). Si hay cambios sin
# commitear en fantasma/viz/ (HUD) o fantasma/ui/ (Streamlit), frena el cierre y
# manda hacer el QA visual ANTES de dar por terminado. Mariana NO detecta sola si
# algo se ve mal (limite semantico: eso es juicio humano); solo OBLIGA a mirarlo.
# Auto-terminante: usa un marcador con el hash del diff ya revisado a ojo
# (.claude/.mariana-marker, gitignored) para no re-pedir lo mismo. Ver ADR 0011.
# Archivo ASCII (sin acentos) a proposito.

$ErrorActionPreference = 'SilentlyContinue'

# Evitar bucle si este stop ya viene de un stop-hook.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }

# Hay cambios visuales sin commitear (HUD o UI)?
$vizChanged = (git status --porcelain -- fantasma/viz fantasma/ui) | Where-Object { $_ }
if (-not $vizChanged) { exit 0 }

# Hash del estado visual actual (diff rastreado + lista de cambios).
$payload = ((git diff HEAD -- fantasma/viz fantasma/ui) -join "`n") + "|" + (($vizChanged) -join "`n")
$sha1 = New-Object System.Security.Cryptography.SHA1Managed
$sha = [System.BitConverter]::ToString($sha1.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload))).Replace('-','')

$marker = Join-Path (Get-Location) ".claude\.mariana-marker"
$last = if (Test-Path $marker) { (Get-Content $marker -Raw).Trim() } else { '' }
if ($sha -eq $last) { exit 0 }   # este diff visual exacto ya se reviso a ojo

$ctx = "Rol Mariana (UX visual): tocaste fantasma/viz/ (HUD) o fantasma/ui/ (UI). " +
       "Antes de cerrar, completa la checklist de QA visual (docs/ux-patterns.md sec 2-B): " +
       "[1] El cambio respeta las 10 heuristicas de Nielsen del dominio (sec 1). " +
       "[2] La pantalla afectada se ve coherente con el resto (espaciado, tipografia, iconos). " +
       "[3] El HUD (si aplica) es legible sobre video real, con la jerarquia piloto/ref correcta. " +
       "[4] Ningun texto en jerga de sistema; vocabulario de pista. " +
       "[5] Estados visibles: carga, progreso, encoder/tiempo, errores claros. " +
       "Abre 'fantasma ui' o revisa el render del HUD con el material de test real. " +
       "Mariana es un checkpoint que vuelve al PO; no juzga sola lo visual. " +
       "Cuando el PO apruebe, marca este diff como revisado ejecutando exactamente: " +
       "Set-Content -Encoding ASCII '.claude/.mariana-marker' '$sha'"
$out = @{
  decision = 'block'
  reason   = 'Cambio visual sin QA (Mariana). Revisar la UI/HUD a ojo antes de cerrar.'
  hookSpecificOutput = @{ hookEventName = 'Stop'; additionalContext = $ctx }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
