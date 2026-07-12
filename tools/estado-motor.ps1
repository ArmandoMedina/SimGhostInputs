#Requires -Version 5
# estado-motor.ps1 - AVISO de divergencia del motor (NO bloquea; exit 0 siempre).
# Lee el sello tools/jidoka-motor.json (de que version de Jidoka viene esta
# maquinaria) y, si hay un checkout de Jidoka a la vista, compara contra su
# tools/version.txt para decir si estas al dia o atras.
#   -Jidoka <ruta>   ruta al repo Jidoka (si no se pasa, usa $env:JIDOKA_HOME)
#   -Detallado       ademas de la version, compara PIEZA POR PIEZA (por hash) contra
#                    el motor actual de Jidoka y lista las que DIVERGEN o faltan.
# Es aviso, no muro (regla 2-3 antes de endurecer): informa y deja decidir al humano.
# Se siembra en cada hijo (motor). Nota: archivo ASCII a proposito, PS 5.1.

param([string]$Jidoka = '', [switch]$Detallado)

$raiz = Split-Path -Parent $PSScriptRoot
$selloPath = Join-Path $raiz 'tools/jidoka-motor.json'

# SHA256 del contenido normalizado a LF (sin CR): agnostico al fin de linea, igual
# que el instalador -- si no, un hijo LF diverge de un Jidoka CRLF por puro EOL (ADR 0021).
function Get-MotorHash($path) {
  $bytes = [System.IO.File]::ReadAllBytes($path)
  $sinCR = New-Object System.Collections.Generic.List[byte]
  foreach ($b in $bytes) { if ($b -ne 13) { $sinCR.Add($b) } }
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try { $h = $sha.ComputeHash($sinCR.ToArray()) } finally { $sha.Dispose() }
  return ([System.BitConverter]::ToString($h) -replace '-', '')
}

Write-Host "== Estado del motor Jidoka =="
if (-not (Test-Path $selloPath)) {
  Write-Host "  [AVISO] no hay sello (tools/jidoka-motor.json): no se de que version viene tu maquinaria." -ForegroundColor Yellow
  Write-Host "          Si convergiste el motor a mano, sellalo (desde Jidoka): ./tools/instalar.ps1 -Destino '$raiz' -Sellar"
  exit 0
}
$sello = Get-Content $selloPath -Raw | ConvertFrom-Json
$mia = $sello.version
Write-Host "  Tu motor: Jidoka $mia"

if (-not $Jidoka) { $Jidoka = $env:JIDOKA_HOME }
if (-not $Jidoka) {
  Write-Host "  (no hay un checkout de Jidoka a la vista: pasa -Jidoka <ruta> o exporta JIDOKA_HOME para comparar.)"
  exit 0
}
$verJidokaPath = Join-Path $Jidoka 'tools/version.txt'
if (-not (Test-Path $verJidokaPath)) {
  Write-Host "  (no encuentro tools/version.txt en '$Jidoka': no puedo comparar.)" -ForegroundColor Yellow
  exit 0
}
$suya = (Get-Content $verJidokaPath -Raw).Trim()
Write-Host "  Jidoka actual: $suya"

if ($mia -eq $suya) {
  Write-Host "  [OK] Tu maquinaria declara la version de Jidoka $suya." -ForegroundColor Green
}
else {
  Write-Host "  [AVISO] Tu sello ($mia) difiere de Jidoka ($suya): probablemente estas atras." -ForegroundColor Yellow
  Write-Host "          Baja la mecanica (desde el repo Jidoka, apuntando aca):"
  Write-Host "            ./tools/instalar.ps1 -Destino '$raiz' -Actualizar"
  Write-Host "          Corre en una rama -> revisa el diff -> PR (el diff ES la revision)."
}

# -Detallado: la version del sello es de grano grueso (no ve la divergencia por-pieza).
# Aqui se compara cada pieza de mecanica del manifiesto de Jidoka contra la del hijo,
# por hash, y se listan las que DIVERGEN o faltan (las al dia solo se cuentan: menos ruido).
if ($Detallado) {
  $manifPath = Join-Path $Jidoka 'kit/.jidoka/instalar/manifiesto.json'
  if (-not (Test-Path $manifPath)) {
    Write-Host "  (no encuentro el manifiesto en '$Jidoka': no puedo detallar por-pieza.)" -ForegroundColor Yellow
    exit 0
  }
  $manif = Get-Content $manifPath -Raw | ConvertFrom-Json
  Write-Host ""
  Write-Host "  Detalle por pieza (mecanica) vs Jidoka $($suya):"
  $alDia = 0; $div = 0; $aus = 0
  foreach ($e in $manif.motor) {
    if ($e.clase -and $e.clase -ne 'mecanica') { continue }
    $srcRoot = Join-Path $Jidoka $e.origen
    if (-not (Test-Path -LiteralPath $srcRoot)) { continue }
    $pares = @()
    if ($e.dir) {
      Get-ChildItem -LiteralPath $srcRoot -Recurse -File | ForEach-Object {
        $relEnOrigen = $_.FullName.Substring($srcRoot.Length).TrimStart('\', '/').Replace('\', '/')
        $relDst = ($e.destino.Replace('\', '/')).TrimEnd('/') + '/' + $relEnOrigen
        $pares += [pscustomobject]@{ rel = $relDst; src = $_.FullName }
      }
    } else {
      $pares += [pscustomobject]@{ rel = $e.destino.Replace('\', '/'); src = $srcRoot }
    }
    foreach ($par in $pares) {
      $childAbs = Join-Path $raiz $par.rel
      if (-not (Test-Path -LiteralPath $childAbs)) { Write-Host ("    [AUSENTE]  {0}" -f $par.rel) -ForegroundColor Yellow; $aus++; continue }
      $jh = Get-MotorHash $par.src
      $ch = Get-MotorHash $childAbs
      if ($ch -eq $jh) { $alDia++ }
      else { Write-Host ("    [DIVERGE]  {0}" -f $par.rel) -ForegroundColor Yellow; $div++ }
    }
  }
  Write-Host ("  Resumen por pieza: {0} al dia | {1} divergen | {2} ausente(s)." -f $alDia, $div, $aus) -ForegroundColor Cyan
  if ($div -gt 0) { Write-Host "  (las divergentes son customizaciones tuyas o piezas atras; -Actualizar preserva lo customizado y baja lo pristino.)" }
}
exit 0
