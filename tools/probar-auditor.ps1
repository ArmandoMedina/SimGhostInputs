#Requires -Version 5
# probar-auditor.ps1 - prueba de vida del auditor del grafo (disparo
# prueba-de-vida-del-gate). Corre tools/auditar.ps1 -Repo <tmp> -Bloquea contra
# grafos sinteticos de resultado conocido, incluidos los que DEBEN bloquear
# (sin frontmatter, wikilink roto, capacidad vigente sin Gherkin) y uno valido.
#
# Uso:  ./tools/probar-auditor.ps1   (exit 0 = auditor sano; exit 1 = tiene un bug)
# Nota: archivo ASCII a proposito, PS 5.1.

$auditar = Join-Path $PSScriptRoot 'auditar.ps1'
$script:fallos = 0
$script:casos = 0

function Check($nombre, $cond, $detalle) {
  $script:casos++
  if ($cond) { Write-Host "  [PASA]  $nombre" -ForegroundColor Green }
  else { Write-Host "  [FALLA] $nombre ($detalle)" -ForegroundColor Red; $script:fallos++ }
}

function New-Graph {
  $dir = Join-Path $env:TEMP ("jidoka-auditest-" + [guid]::NewGuid().ToString('N').Substring(0,8))
  New-Item -ItemType Directory -Path (Join-Path $dir 'product/capacidades') -Force | Out-Null
  return $dir
}
function Write-Note($repo, $rel, $content) {
  $p = Join-Path $repo $rel
  New-Item -ItemType Directory -Path (Split-Path -Parent $p) -Force | Out-Null
  Set-Content -Path $p -Value $content -Encoding UTF8
}
function Run($repo) {
  $out = (powershell -NoProfile -ExecutionPolicy Bypass -File $auditar -Repo $repo -Bloquea 2>&1 | Out-String)
  return @{ out = $out; code = $LASTEXITCODE }
}

$capValida = @"
---
tipo: capacidad
estado: vigente
clave: CAP-1
modulo: MOD-1
dominio: Dominio de prueba
---
# Capacidad de prueba

## Criterios de aceptacion

- Dado que existe una entrada, cuando corre, entonces produce salida.

No existe test aun.
"@

Write-Host "== Prueba de vida del auditor del grafo (tools/auditar.ps1) =="

# 1. Grafo valido: capacidad vigente completa -> sin BLOQUEA (exit 0).
$g = New-Graph
Write-Note $g 'product/capacidades/CAP-1.md' $capValida
$r = Run $g
Check 'valido: capacidad vigente completa no bloquea' ($r.code -eq 0 -and -not $r.out.Contains('[BLOQUEA]')) "code=$($r.code) out=$($r.out)"
Remove-Item $g -Recurse -Force -ErrorAction SilentlyContinue

# 2. Sin frontmatter -> BLOQUEA.
$g = New-Graph
Write-Note $g 'product/capacidades/mala.md' "# Sin frontmatter`n`nsolo texto"
$r = Run $g
Check 'bloquea: nota sin frontmatter YAML' ($r.code -eq 1 -and $r.out.Contains('sin frontmatter')) "code=$($r.code) out=$($r.out)"
Remove-Item $g -Recurse -Force -ErrorAction SilentlyContinue

# 3. Wikilink roto -> BLOQUEA.
$g = New-Graph
Write-Note $g 'product/capacidades/CAP-2.md' "---`ntipo: capacidad`nestado: en_definicion`nclave: CAP-2`nmodulo: MOD-1`ndominio: X`n---`n# C2`n`nver [[no-existe-esta-nota]]"
$r = Run $g
Check 'bloquea: wikilink roto' ($r.code -eq 1 -and $r.out.Contains('wikilink roto')) "code=$($r.code) out=$($r.out)"
Remove-Item $g -Recurse -Force -ErrorAction SilentlyContinue

# 4. Capacidad vigente sin criterios Gherkin -> BLOQUEA.
$g = New-Graph
Write-Note $g 'product/capacidades/CAP-3.md' "---`ntipo: capacidad`nestado: vigente`nclave: CAP-3`nmodulo: MOD-1`ndominio: X`n---`n# C3`n`nsin criterios."
$r = Run $g
Check 'bloquea: capacidad vigente sin criterios de aceptacion' ($r.code -eq 1 -and $r.out.Contains('Criterios de aceptacion')) "code=$($r.code) out=$($r.out)"
Remove-Item $g -Recurse -Force -ErrorAction SilentlyContinue

# 5. Modulacion por estado: en_definicion sin criterios NO bloquea (solo consistencia).
$g = New-Graph
Write-Note $g 'product/capacidades/CAP-4.md' "---`ntipo: capacidad`nestado: en_definicion`nclave: CAP-4`nmodulo: MOD-1`ndominio: X`n---`n# C4`n`nen exploracion, sin criterios aun."
$r = Run $g
Check 'modula: capacidad en_definicion sin criterios no bloquea' ($r.code -eq 0 -and -not $r.out.Contains('[BLOQUEA]')) "code=$($r.code) out=$($r.out)"
Remove-Item $g -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
if ($script:fallos -gt 0) {
  Write-Host "== $($script:fallos) de $($script:casos) caso(s) fallidos. El auditor tiene un bug: no lo estrenes. ==" -ForegroundColor Red
  exit 1
}
Write-Host "== Auditor sano: los $($script:casos) casos se comportan como se espera. ==" -ForegroundColor Green
exit 0
