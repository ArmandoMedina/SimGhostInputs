#Requires -Version 5
# probar-hooks.ps1 - prueba de vida de los hooks (disparo prueba-de-vida-del-gate:
# un hook no se estrena sin correrlo contra escenarios de resultado conocido,
# incluido uno que DEBE bloquear). Complementa a probar-gate.ps1 (que prueba el
# verificador). Prueba no-memorias por stdin y los Stop-hooks review/gemba en un
# repo git TEMPORAL con el estado exacto que dispara cada caso.
#
# Uso:  ./tools/probar-hooks.ps1   (exit 0 = hooks sanos; exit 1 = un hook tiene un bug)
# Nota: archivo ASCII a proposito (sin acentos), PS 5.1.

$hooksDir = Join-Path (Split-Path -Parent $PSScriptRoot) '.claude/hooks'
$script:fallos = 0
$script:casos = 0

function Check($nombre, $cond, $detalle) {
  $script:casos++
  if ($cond) { Write-Host "  [PASA]  $nombre" -ForegroundColor Green }
  else { Write-Host "  [FALLA] $nombre ($detalle)" -ForegroundColor Red; $script:fallos++ }
}

# Corre un hook alimentando stdin JSON como PROCESO hijo (asi [Console]::In lo lee),
# opcionalmente con CLAUDE_PROJECT_DIR apuntando a un repo de prueba.
function Invoke-Hook($hookPath, $stdinJson, $projectDir) {
  $prev = $env:CLAUDE_PROJECT_DIR
  if ($projectDir) { $env:CLAUDE_PROJECT_DIR = $projectDir }
  try { $out = ($stdinJson | powershell -NoProfile -ExecutionPolicy Bypass -File $hookPath 2>&1 | Out-String) }
  finally { $env:CLAUDE_PROJECT_DIR = $prev }
  return $out
}

function New-TempRepo {
  $dir = Join-Path $env:TEMP ("jidoka-hooktest-" + [guid]::NewGuid().ToString('N').Substring(0,8))
  New-Item -ItemType Directory -Path $dir -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $dir 'tools') -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $dir '.claude') -Force | Out-Null
  Push-Location $dir
  git init -q 2>&1 | Out-Null
  git config user.email "test@jidoka.local" 2>&1 | Out-Null
  git config user.name "jidoka-test" 2>&1 | Out-Null
  git config commit.gpgsign false 2>&1 | Out-Null
  Pop-Location
  return $dir
}

function Set-Manifest($repo, $json) { Set-Content -Path (Join-Path $repo 'tools/blast-radius.json') -Value $json -Encoding Ascii }

Write-Host "== Prueba de vida de los hooks (.claude/hooks) =="

# --- no-memorias (PreToolUse, stdin-driven) ---
$noMem = Join-Path $hooksDir 'no-memorias-pretooluse.ps1'
$outDeny = Invoke-Hook $noMem '{"tool_input":{"file_path":"C:\\Users\\x\\.claude\\projects\\slug\\memory\\foo.md"}}' $null
Check 'no-memorias: DENIEGA escritura a la carpeta de memoria' ($outDeny.Contains('"permissionDecision":"deny"')) "no denego: $outDeny"
$outAllow = Invoke-Hook $noMem '{"tool_input":{"file_path":"C:\\repo\\HANDOFF.md"}}' $null
Check 'no-memorias: DEJA pasar una ruta normal del repo' (-not $outAllow.Contains('deny')) "denego de mas: $outAllow"

# Grieta 2 (auditoria externa): el bypass por Bash. Antes el matcher era solo Write|Edit
# y un Set-Content/redireccion por Bash rodeaba el deny. Ahora se inspecciona
# tool_input.command: ESCRITURA a la memoria bloquea; LECTURA (recall) no.
$outBashSet = Invoke-Hook $noMem '{"tool_name":"Bash","tool_input":{"command":"Set-Content -Path C:\\Users\\x\\.claude\\projects\\slug\\memory\\foo.md -Value hola"}}' $null
Check 'no-memorias: DENIEGA escritura a memoria por Bash (Set-Content)' ($outBashSet.Contains('"permissionDecision":"deny"')) "no denego el bypass: $outBashSet"
$outBashRedir = Invoke-Hook $noMem '{"tool_name":"Bash","tool_input":{"command":"echo hola > ~/.claude/projects/slug/memory/foo.md"}}' $null
Check 'no-memorias: DENIEGA escritura a memoria por Bash (redireccion >)' ($outBashRedir.Contains('"permissionDecision":"deny"')) "no denego el redirect: $outBashRedir"
$outBashRead = Invoke-Hook $noMem '{"tool_name":"Bash","tool_input":{"command":"cat C:\\Users\\x\\.claude\\projects\\slug\\memory\\foo.md"}}' $null
Check 'no-memorias: DEJA LEER memoria por Bash (recall no se bloquea)' (-not $outBashRead.Contains('deny')) "bloqueo una lectura: $outBashRead"
$outBashNorm = Invoke-Hook $noMem '{"tool_name":"Bash","tool_input":{"command":"Set-Content -Path C:\\repo\\HANDOFF.md -Value hi"}}' $null
Check 'no-memorias: DEJA pasar una escritura Bash normal del repo' (-not $outBashNorm.Contains('deny')) "denego de mas por Bash: $outBashNorm"
# Regresion v1.1.0: el token '>' casaba con '2>&1'/'2>/dev/null' (redireccion de stderr,
# NO escritura a memoria) y bloqueaba lecturas comunes. Deben DEJAR pasar.
$outBashErr1 = Invoke-Hook $noMem '{"tool_name":"Bash","tool_input":{"command":"cat ~/.claude/projects/slug/memory/foo.md 2>&1"}}' $null
Check 'no-memorias: DEJA LEER memoria con 2>&1 (no es escritura)' (-not $outBashErr1.Contains('deny')) "falso positivo 2>&1: $outBashErr1"
$outBashErr2 = Invoke-Hook $noMem '{"tool_name":"Bash","tool_input":{"command":"ls -1 ~/.claude/projects/slug/memory/ 2>/dev/null"}}' $null
Check 'no-memorias: DEJA LISTAR memoria con 2>/dev/null (no es escritura)' (-not $outBashErr2.Contains('deny')) "falso positivo 2>/dev/null: $outBashErr2"

# --- stop_hook_active: los Stop-hooks no re-bloquean ---
foreach ($h in @('review-stop.ps1','gemba-stop.ps1','andon-stop.ps1')) {
  $o = Invoke-Hook (Join-Path $hooksDir $h) '{"stop_hook_active":true}' $null
  Check "${h}: respeta stop_hook_active (no re-bloquea)" (-not $o.Contains('"decision":"block"')) "bloqueo en re-entrada: $o"
}

# --- review-stop en repo temporal ---
$r1 = New-TempRepo
Set-Manifest $r1 '[{"nombre":"motor","desc":"x","fuente":["tools/*"],"doc_bloquea":[],"doc_avisa":[],"revisa":true,"rol":"x"}]'
Set-Content (Join-Path $r1 'tools/motor.ps1') "# v1" -Encoding Ascii
Push-Location $r1; git add -A 2>&1 | Out-Null; git commit -q -m init 2>&1 | Out-Null; Pop-Location
# Caso BLOQUEA: codigo (tools/*) modificado sin marcador de revision.
Set-Content (Join-Path $r1 'tools/motor.ps1') "# v2 cambiado" -Encoding Ascii
$oBlock = Invoke-Hook (Join-Path $hooksDir 'review-stop.ps1') '{}' $r1
Check 'review-stop: BLOQUEA codigo sin /code-review' ($oBlock.Contains('"decision":"block"') -and $oBlock.Contains('code-review')) "no bloqueo: $oBlock"
# Caso PASA: sin codigo sin commitear (todo commiteado).
Push-Location $r1; git add -A 2>&1 | Out-Null; git commit -q -m v2 2>&1 | Out-Null; Pop-Location
$oPass = Invoke-Hook (Join-Path $hooksDir 'review-stop.ps1') '{}' $r1
Check 'review-stop: DEJA cerrar sin codigo pendiente' (-not $oPass.Contains('"decision":"block"')) "bloqueo indebido: $oPass"
Remove-Item $r1 -Recurse -Force -ErrorAction SilentlyContinue

# --- gemba-stop en repo temporal ---
$r2 = New-TempRepo
New-Item -ItemType Directory -Path (Join-Path $r2 'ui') -Force | Out-Null
Set-Manifest $r2 '[{"nombre":"ui","desc":"x","fuente":["ui/*"],"doc_bloquea":[],"doc_avisa":[],"rol":"revisor-visual"}]'
Set-Content (Join-Path $r2 'ui/app.js') "// v1" -Encoding Ascii
Push-Location $r2; git add -A 2>&1 | Out-Null; git commit -q -m init 2>&1 | Out-Null; Pop-Location
# Caso BLOQUEA: cambio visual sin evidencia fresca en qa_runs/.
Set-Content (Join-Path $r2 'ui/app.js') "// v2 cambio visual" -Encoding Ascii
$oVBlock = Invoke-Hook (Join-Path $hooksDir 'gemba-stop.ps1') '{}' $r2
Check 'gemba-stop: BLOQUEA cambio visual sin evidencia' ($oVBlock.Contains('"decision":"block"') -and $oVBlock.Contains('qa_runs')) "no bloqueo: $oVBlock"
# Caso BLOQUEA (Goodhart): evidencia fresca por mtime pero NO rastreada por git.
# qa_runs/ esta gitignoreado; un archivo sin 'git add -f' satisface el mtime pero git
# nunca lo vera -- no vale (evidencia-no-palabra: existe en git, no solo en disco).
Set-Content (Join-Path $r2 '.gitignore') "qa_runs/" -Encoding Ascii
$qa = Join-Path $r2 'qa_runs/gemba-prueba'
New-Item -ItemType Directory -Path $qa -Force | Out-Null
$log = Join-Path $qa 'LOG.md'
Set-Content $log "corrida" -Encoding Ascii
(Get-Item $log).LastWriteTime = (Get-Date).AddMinutes(5)   # fresca por mtime, pero sin trackear
$oVUntracked = Invoke-Hook (Join-Path $hooksDir 'gemba-stop.ps1') '{}' $r2
Check 'gemba-stop: BLOQUEA evidencia fresca pero NO rastreada por git (Goodhart)' ($oVUntracked.Contains('"decision":"block"')) "no bloqueo evidencia no-commiteada: $oVUntracked"
# Caso PASA: la misma evidencia, ahora forzada al indice con git add -f.
Push-Location $r2; git add -f qa_runs/gemba-prueba/LOG.md 2>&1 | Out-Null; Pop-Location
(Get-Item $log).LastWriteTime = (Get-Date).AddMinutes(5)   # re-garantiza mtime posterior al cambio
$oVPass = Invoke-Hook (Join-Path $hooksDir 'gemba-stop.ps1') '{}' $r2
Check 'gemba-stop: DEJA cerrar con evidencia rastreada y fresca (git add -f)' (-not $oVPass.Contains('"decision":"block"')) "bloqueo indebido: $oVPass"
Remove-Item $r2 -Recurse -Force -ErrorAction SilentlyContinue

# --- gemba-stop DORMIDO: sin area rol revisor-visual, no dispara ---
$r3 = New-TempRepo
New-Item -ItemType Directory -Path (Join-Path $r3 'ui') -Force | Out-Null
Set-Manifest $r3 '[{"nombre":"ui","desc":"x","fuente":["ui/*"],"doc_bloquea":[],"doc_avisa":[],"rol":"Escribano"}]'
Set-Content (Join-Path $r3 'ui/app.js') "// v1" -Encoding Ascii
Push-Location $r3; git add -A 2>&1 | Out-Null; git commit -q -m init 2>&1 | Out-Null; Pop-Location
Set-Content (Join-Path $r3 'ui/app.js') "// v2" -Encoding Ascii
$oDorm = Invoke-Hook (Join-Path $hooksDir 'gemba-stop.ps1') '{}' $r3
Check 'gemba-stop: DORMIDO si no hay area revisor-visual' (-not $oDorm.Contains('"decision":"block"')) "bloqueo estando dormido: $oDorm"
Remove-Item $r3 -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
if ($script:fallos -gt 0) {
  Write-Host "== $($script:fallos) de $($script:casos) caso(s) fallidos. Un hook tiene un bug: no lo estrenes. ==" -ForegroundColor Red
  exit 1
}
Write-Host "== Hooks sanos: los $($script:casos) casos se comportan como se espera. ==" -ForegroundColor Green
exit 0
