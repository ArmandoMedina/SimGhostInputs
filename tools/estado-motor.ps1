#Requires -Version 5
# estado-motor.ps1 - AVISO de divergencia del motor (NO bloquea; exit 0 siempre).
# Lee el sello tools/jidoka-motor.json (de que version de Jidoka viene esta
# maquinaria) y, si hay un checkout de Jidoka a la vista, compara contra su
# tools/version.txt para decir si estas al dia o atras.
#   -Jidoka <ruta>   ruta al repo Jidoka (si no se pasa, usa $env:JIDOKA_HOME)
# Es aviso, no muro (regla 2-3 antes de endurecer): informa y deja decidir al humano.
# Se siembra en cada hijo (motor). Nota: archivo ASCII a proposito, PS 5.1.

param([string]$Jidoka = '')

$raiz = Split-Path -Parent $PSScriptRoot
$selloPath = Join-Path $raiz 'tools/jidoka-motor.json'

Write-Host "== Estado del motor Jidoka =="
if (-not (Test-Path $selloPath)) {
  Write-Host "  [AVISO] no hay sello (tools/jidoka-motor.json): no se de que version viene tu maquinaria." -ForegroundColor Yellow
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
  Write-Host "  [OK] Tu maquinaria esta al dia con Jidoka $suya." -ForegroundColor Green
}
else {
  Write-Host "  [AVISO] Tu sello ($mia) difiere de Jidoka ($suya): probablemente estas atras." -ForegroundColor Yellow
  Write-Host "          Baja la mecanica (desde el repo Jidoka, apuntando aca):"
  Write-Host "            ./tools/instalar.ps1 -Destino '$raiz' -Actualizar"
  Write-Host "          Corre en una rama -> revisa el diff -> PR (el diff ES la revision)."
}
exit 0
