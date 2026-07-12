#Requires -Version 5
# probar-disparos.ps1 - prueba de vida del REGISTRO de disparos cableados (grieta 5).
# El catalogo kit/.jidoka/disparos/README.md declara, por disparo, "Cableado en: <path>"
# (su punto de inyeccion real) o "Catalogo-solo: <razon>". Este self-test verifica que
# cada "Cableado en" siga presente en su punto (el archivo existe y NOMBRA el slug) --
# asi el cableado no se pudre en silencio, que era la grieta real (no que faltara
# cablear, sino que nada lo comprobaba). Incluye un caso sintetico que DEBE detectar
# rot: quien valida tambien se valida (disparo prueba-de-vida-del-gate).
#
# Uso:  ./tools/probar-disparos.ps1   (exit 0 = registro sano; exit 1 = un cableado se pudrio)
# Nota: archivo ASCII a proposito (sin acentos), PS 5.1.

$repoRoot = Split-Path -Parent $PSScriptRoot
$catalog  = Join-Path $repoRoot 'kit/.jidoka/disparos/README.md'
$script:fallos = 0
$script:casos = 0

function Check($nombre, $cond, $detalle) {
  $script:casos++
  if ($cond) { Write-Host "  [PASA]  $nombre" -ForegroundColor Green }
  else { Write-Host "  [FALLA] $nombre ($detalle)" -ForegroundColor Red; $script:fallos++ }
}

# Parsea un catalogo y verifica los "Cableado en" contra $root. Devuelve un hash:
# @{ total; cableados; catalogo; problemas = @(...) }. Un slug es una cabecera
# '### kebab-case' en su propia linea (asi '### Catalogo v0' no cuenta como disparo).
# Un punto de inyeccion ausente NO es rot: es un punto que ESTE install no sembro
# (p.ej. un hijo sin el PR template). Se OMITE con aviso visible (sin descartes
# silenciosos) en vez de fallar. El rot real -- el archivo existe pero ya no nombra
# el slug -- si falla. Asi el check es portable: en Jidoka estan los 10 puntos
# (0 omitidos, rigor total); en un hijo verifica lo que sembro y avisa lo que no.
function Test-Registro($catalogPath, $root) {
  $lineas = Get-Content -LiteralPath $catalogPath
  $slug = $null
  $total = 0; $cableados = 0; $catalogo = 0
  $problemas = @(); $omitidos = @()
  foreach ($ln in $lineas) {
    if ($ln -match '^###\s+([a-z0-9-]+)\s*$') {
      if ($slug) { $problemas += "$slug (sin linea de estado Cableado/Catalogo)" }
      $slug = $Matches[1]; $total++; continue
    }
    if (-not $slug) { continue }
    if ($ln -match '\*\*Cableado en:\*\*\s*`([^`]+)`') {
      $cableados++
      $rel = $Matches[1].Trim()
      $abs = Join-Path $root $rel
      if (-not (Test-Path -LiteralPath $abs)) {
        $omitidos += "$slug -> $rel (no sembrado en este install; omitido)"
      } elseif (-not ((Get-Content -LiteralPath $abs -Raw) -match [regex]::Escape($slug))) {
        $problemas += "$slug -> $rel (el punto de inyeccion no nombra el slug: cableado podrido)"
      }
      $slug = $null; continue
    }
    if ($ln -match '\*\*Catalogo-solo:\*\*\s*(\S.*)?$') {
      $catalogo++
      if (-not $Matches[1]) { $problemas += "$slug (Catalogo-solo sin razon)" }
      $slug = $null; continue
    }
  }
  if ($slug) { $problemas += "$slug (sin linea de estado Cableado/Catalogo)" }
  return @{ total = $total; cableados = $cableados; catalogo = $catalogo; problemas = $problemas; omitidos = $omitidos }
}

Write-Host "== Prueba de vida del registro de disparos (kit/.jidoka/disparos) =="

# --- El catalogo REAL: cada disparo con estado, cada Cableado presente en su punto. ---
$r = Test-Registro $catalog $repoRoot
Check "catalogo real: todos los disparos con estado y cada Cableado presente nombra su slug" ($r.problemas.Count -eq 0) ($r.problemas -join ' | ')
Check "catalogo real: se leyeron los 12 disparos del catalogo v0" ($r.total -ge 12) "leidos: $($r.total)"
Write-Host ("  ({0} disparos: {1} cableados, {2} catalogo-solo)" -f $r.total, $r.cableados, $r.catalogo) -ForegroundColor DarkGray
foreach ($o in $r.omitidos) { Write-Host "  [OMITIDO] $o" -ForegroundColor Yellow }

# --- Caso sintetico que DEBE detectar rot: un Cableado cuyo punto NO nombra el slug. ---
$tmp = Join-Path $env:TEMP ("jidoka-disparos-prueba-" + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
  Set-Content -Path (Join-Path $tmp 'punto-sano.ps1') "# aqui vive el disparo prueba-sana" -Encoding Ascii
  Set-Content -Path (Join-Path $tmp 'punto-podrido.ps1') "# este archivo ya NO menciona su disparo" -Encoding Ascii
  $catSint = Join-Path $tmp 'catalogo.md'
  @'
# Catalogo sintetico

### prueba-sana
> texto
**Cableado en:** `punto-sano.ps1`

### prueba-podrida
> texto
**Cableado en:** `punto-podrido.ps1`
'@ | Set-Content -Path $catSint -Encoding Ascii

  $s = Test-Registro $catSint $tmp
  $cazoPodrido = @($s.problemas | Where-Object { $_ -match 'prueba-podrida' -and $_ -match 'podrido' }).Count -eq 1
  $dejoSana    = -not (@($s.problemas | Where-Object { $_ -match 'prueba-sana' }).Count)
  Check 'sintetico: DETECTA el cableado podrido (punto que no nombra el slug)' $cazoPodrido "problemas: $($s.problemas -join ' | ')"
  Check 'sintetico: NO marca el cableado sano' $dejoSana "marco de mas: $($s.problemas -join ' | ')"
}
finally { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host ""
if ($script:fallos -gt 0) {
  Write-Host "== $($script:fallos) de $($script:casos) caso(s) fallidos. El registro de disparos tiene un cableado podrido. ==" -ForegroundColor Red
  exit 1
}
Write-Host "== Registro sano: los $($script:casos) casos se comportan como se espera. ==" -ForegroundColor Green
exit 0
