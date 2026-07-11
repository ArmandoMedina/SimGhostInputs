# andon-stop.ps1 - Stop hook. Si al cerrar hay doc-drift (segun la ley,
# tools/blast-radius.json), frena el cierre y manda al Escribano a sincronizar.
# Cuando todos los docs duenos estan sincronizados, el hook deja cerrar solo.
# Jidoka corre su propio Andon (dogfooding). Archivo ASCII (sin acentos) a proposito.
#
# VENTANA: este hook evalua git status --porcelain (cambios SIN commitear).
# El gate de push (verificar.ps1) evalua @{u}..HEAD (commiteado sin pushear).
# Si committeas sin docs, esta ventana ya no detecta el drift: lo atrapan
# verificar.ps1 al push y el CI (andon.yml) sobre el rango del PR.
#
# Matcher: comodines -like; un patron SIN '/' solo casa archivos en la raiz del
# repo; 'excluye' (opcional) resta rutas; 'mensaje' (opcional) se anexa al aviso.

$ErrorActionPreference = 'Continue'

# ALTO-04 (leccion del laboratorio de campo): cada git real revisa $LASTEXITCODE.
# Si git falla de verdad (no instalado, repo corrupto), se AVISA en vez de callar:
# tratar un fallo como "sin cambios" es un gate podrido en silencio. El hook no
# bloquea por esto (es aviso); los que fallan cerrado son verificar.ps1 y el CI.
function Avisa-SinVeredicto($detalle) {
  $out = @{
    hookSpecificOutput = @{
      hookEventName     = 'Stop'
      additionalContext = "[AVISO] andon-stop no pudo medir: $detalle. El gate de cierre queda sin veredicto esta vez; verificar.ps1 (pre-push) y el CI si fallan cerrado."
    }
  }
  $out | ConvertTo-Json -Compress -Depth 5
  exit 0
}

# 1. Leer el input del hook. Si este stop YA viene de un stop-hook, no re-bloquear.
$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { $inp = $null }
if ($inp -and $inp.stop_hook_active) { exit 0 }

# 2. Obtener lista de archivos con cambios sin commitear.
if ($env:CLAUDE_PROJECT_DIR) { Set-Location $env:CLAUDE_PROJECT_DIR }
$repoRaw = git rev-parse --show-toplevel 2>&1
if ($LASTEXITCODE -ne 0) { Avisa-SinVeredicto "git rev-parse fallo o no hay repo ($("$repoRaw".Trim() -split "`n" | Select-Object -First 1))" }
$repo = "$repoRaw".Trim()
$statusRaw = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) { Avisa-SinVeredicto "git status fallo ($("$statusRaw".Trim() -split "`n" | Select-Object -First 1))" }
$changed = @($statusRaw) | ForEach-Object { $s = "$_"; if ($s.Length -gt 3) { $s.Substring(3).Trim() } }
if (-not $changed) { exit 0 }

# 3. Leer el manifiesto unico de blast-radius (la ley).
$manifestPath = Join-Path $repo 'tools/blast-radius.json'
if (-not (Test-Path $manifestPath)) { exit 0 }
try { $manifest = Get-Content $manifestPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop }
catch { Avisa-SinVeredicto "la ley tools/blast-radius.json no se pudo leer o parsear" }

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
  foreach ($tgt in $entry.doc_avisa) {
    if ($tgt -and -not (Match-Any $changed $tgt)) {
      $linea = "area '$($entry.nombre)': revisa '$tgt' (rol $($entry.rol))"
      if ($entry.mensaje) { $linea += " - $($entry.mensaje)" }
      $avisos += $linea
    }
  }
  # product_avisa: el grafo de producto. Aviso unico por area si no se toco ninguna nota.
  if ($entry.product_avisa -and $entry.product_avisa.Count -gt 0) {
    $tocoProducto = $false
    foreach ($tgt in $entry.product_avisa) { if (Match-Any $changed $tgt) { $tocoProducto = $true; break } }
    if (-not $tocoProducto) {
      $ej = ($entry.product_avisa | Select-Object -First 2) -join ', '
      $avisos += "area '$($entry.nombre)': tocaste el area sin tocar el grafo de producto (ej: $ej). Si la capacidad cambio, actualiza su nota en product/."
    }
  }
}

# 5. Sin drift en doc_bloquea: dejar cerrar. Con drift: bloquear y mandar al Escribano.
if ($faltas.Count -eq 0) { exit 0 }

$ctx = "Doc-drift (la ley: tools/blast-radius.json). BLOQUEA: " + ($faltas -join '; ') + ". "
if ($avisos.Count -gt 0) { $ctx += "AVISOS no bloqueantes (verificar y el CI los re-verifican): " + (($avisos | Select-Object -First 5) -join '; ') + ". " }
$ctx += "Sincroniza los docs duenos antes de cerrar. Si el cambio implica una DECISION (no solo codigo), " +
        "no la escribas suelta: agrega un ADR en docs/decisions/ y listalo en el indice. " +
        "NOTA: este hook ve cambios sin commitear (working tree). Si ya committeaste sin los docs, " +
        "el drift lo atrapan verificar.ps1 al push y el CI (andon.yml)."
# El texto rico va en 'reason': es el campo que documentadamente llega al modelo
# en un Stop hook (additionalContext no esta documentado para Stop; se conserva
# por si el harness lo aprovecha, pero no se depende de el).
$out = @{
  decision = 'block'
  reason   = $ctx
  hookSpecificOutput = @{
    hookEventName     = 'Stop'
    additionalContext = $ctx
  }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
