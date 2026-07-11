#Requires -Version 5
# auditar.ps1 - Auditor determinista del grafo de documentacion (product/ + engineering/).
# Verifica integridad estructural: frontmatter, wikilinks, criterios de las capacidades
# vigentes y huerfanos. Es el "muro" que corre el CI: un subagente no lo puede saltar
# porque se evalua sobre el ARTEFACTO (los .md del repo), no sobre confiar en el agente.
#
# Complementa al doc-gate de verificar.ps1 (code->doc dueno, seccion 8 de CONTRIBUTING):
# aquel cuida la sincronia codigo<->doc; este cuida que el grafo del QUE/COMO este integro.
#
# Reglas:
#   BLOQUEA - frontmatter ausente/incompleto; wikilink roto; capacidad 'vigente' sin
#             criterios de aceptacion Gherkin.
#   AVISA   - capacidad 'vigente' sin test referenciado ni disclaimer; nota huerfana.
#   Modulacion por estado: 'en_definicion' solo exige frontmatter + enlaces; 'vigente'
#             exige criterios. No estorba la fase de exploracion.
#
# Uso:
#   ./tools/auditar.ps1                    # audita todo el arbol (modo aviso, exit 0)
#   ./tools/auditar.ps1 -Range main..HEAD  # solo las notas tocadas en el rango
#   ./tools/auditar.ps1 -Bloquea           # exit 1 si hay hallazgos BLOQUEA (modo CI)
#
# Archivo ASCII a proposito (sin acentos) para no depender del BOM en PS 5.1; lee los
# .md como UTF-8 para respetar acentos en el contenido y los nombres de archivo.

[CmdletBinding()]
param(
  [string]$Range,
  [switch]$Bloquea,
  [string]$Repo = ''
)

if (-not $Repo) { $Repo = Split-Path -Parent $PSScriptRoot }
$repo = $Repo
Set-Location $repo
$utf8 = New-Object System.Text.UTF8Encoding($false)

$script:block = 0
$script:warn  = 0
function Note($msg)  { Write-Host "  [AVISO] $msg"   -ForegroundColor Yellow; $script:warn++ }
function Block($msg) { Write-Host "  [BLOQUEA] $msg" -ForegroundColor Red;    $script:block++ }

# Parsea el frontmatter YAML simple (key: value) del bloque --- ... --- inicial.
function Get-Frontmatter($text) {
  $lines = $text -split "`r?`n"
  if ($lines.Count -lt 2 -or $lines[0].Trim() -ne '---') { return $null }
  $fm = @{}
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq '---') { return $fm }
    if ($lines[$i] -match '^\s*([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$') {
      $fm[$Matches[1]] = $Matches[2].Trim()
    }
  }
  return $null  # sin cierre ---
}

# Normaliza el destino de un wikilink: [[a|alias]] -> a ; [[a#anchor]] -> a
function Get-WikiTarget($raw) {
  return ((($raw -split '\|')[0]) -split '#')[0].Trim()
}

Write-Host "== Auditar grafo de docs (product/ + engineering/) =="

# --- 1. Indice global de notas (stem -> ruta) para resolver wikilinks ----------
# Destinos validos de un [[wikilink]]: product/, engineering/, docs/ y templates/.
$scanDirs = @('product', 'engineering', 'docs', 'templates')
$allNotes = @()
foreach ($d in $scanDirs) {
  if (Test-Path $d) { $allNotes += Get-ChildItem -Path $d -Recurse -Filter *.md -File }
}
$stemIndex = @{}
foreach ($n in $allNotes) {
  $stemIndex[[System.IO.Path]::GetFileNameWithoutExtension($n.Name)] = $n.FullName
}

# --- 2. Notas a auditar: product/ + engineering/, sin READMEs ------------------
$targets = @()
foreach ($d in @('product', 'engineering')) {
  if (Test-Path $d) {
    $targets += Get-ChildItem -Path $d -Recurse -Filter *.md -File |
      Where-Object { $_.Name -ne 'README.md' }
  }
}

# Filtro por rango: solo las notas tocadas en $Range (para el CI sobre un PR).
if ($Range) {
  $changed = git diff --name-only $Range -- product engineering
  $changedSet = @{}
  foreach ($c in $changed) { $changedSet[$c.Replace('\', '/')] = $true }
  $targets = $targets | Where-Object {
    $changedSet.ContainsKey($_.FullName.Substring($repo.Length + 1).Replace('\', '/'))
  }
}

# --- 3. Auditar cada nota ------------------------------------------------------
foreach ($t in $targets) {
  $rel  = $t.FullName.Substring($repo.Length + 1).Replace('\', '/')
  $text = [System.IO.File]::ReadAllText($t.FullName, $utf8)
  $fm   = Get-Frontmatter $text

  # 3a. Frontmatter + claves requeridas.
  if ($null -eq $fm) { Block "$rel : sin frontmatter YAML valido (--- ... ---)"; continue }
  if (-not $fm.ContainsKey('tipo'))   { Block "$rel : frontmatter sin 'tipo'" }
  if (-not $fm.ContainsKey('estado')) { Block "$rel : frontmatter sin 'estado'" }
  $tipo = $fm['tipo']
  if ($tipo -eq 'capacidad') {
    foreach ($k in @('clave', 'modulo', 'dominio')) {
      if (-not $fm.ContainsKey($k)) { Block "$rel : capacidad sin '$k' en frontmatter" }
    }
  }

  # 3b. Wikilinks rotos.
  foreach ($m in [regex]::Matches($text, '\[\[([^\]]+)\]\]')) {
    $tg = Get-WikiTarget $m.Groups[1].Value
    if ($tg -and -not $stemIndex.ContainsKey($tg)) {
      Block "$rel : wikilink roto [[$tg]] (no existe nota con ese nombre)"
    }
  }

  # 3c. Modulacion por estado (solo capacidades).
  if ($tipo -eq 'capacidad' -and $fm['estado'] -eq 'vigente') {
    if ($text -notmatch '##\s+Criterios de aceptaci') {
      Block "$rel : capacidad vigente sin seccion '## Criterios de aceptacion'"
    }
    elseif ($text -notmatch '(?im)^\s*-?\s*Dado ') {
      Block "$rel : capacidad vigente sin criterios Gherkin (Dado que... cuando... entonces...)"
    }
    $tieneDisclaimer = $text -match '(?i)no existe test'
    $testOk = $false
    foreach ($rt in [regex]::Matches($text, 'tests?[/\\][\w/\\.-]+\.py')) {
      if (Test-Path $rt.Value.Replace('\', '/')) { $testOk = $true; break }
    }
    if (-not $tieneDisclaimer -and -not $testOk) {
      Note "$rel : capacidad vigente sin test referenciado ni disclaimer 'no existe test'"
    }
  }
}

# --- 4. Huerfanos: notas sin ningun enlace entrante [[...]] --------------------
$inbound = @{}
foreach ($t in $targets) { $inbound[[System.IO.Path]::GetFileNameWithoutExtension($t.Name)] = 0 }
foreach ($n in $allNotes) {
  $srcStem = [System.IO.Path]::GetFileNameWithoutExtension($n.Name)
  $txt = [System.IO.File]::ReadAllText($n.FullName, $utf8)
  # Enlaces wiki [[nota]].
  foreach ($m in [regex]::Matches($txt, '\[\[([^\]]+)\]\]')) {
    $tg = Get-WikiTarget $m.Groups[1].Value
    if ($inbound.ContainsKey($tg) -and $tg -ne $srcStem) { $inbound[$tg]++ }
  }
  # Enlaces markdown a otra nota: [texto](ruta/nota.md) - cuentan como entrante
  # (las capas product->engineering se enlazan asi, no con wikilink).
  foreach ($m in [regex]::Matches($txt, '\]\(([^)\s]+\.md)(?:#[^)]*)?\)')) {
    $st = [System.IO.Path]::GetFileNameWithoutExtension([System.Uri]::UnescapeDataString($m.Groups[1].Value))
    if ($inbound.ContainsKey($st) -and $st -ne $srcStem) { $inbound[$st]++ }
  }
}
# Exentos (raices legitimas que nadie tiene por que enlazar hacia abajo).
$exentTipos = @('ecosistema', 'solucion', 'backlog', 'proceso')
foreach ($t in $targets) {
  $stem = [System.IO.Path]::GetFileNameWithoutExtension($t.Name)
  if ($inbound[$stem] -gt 0) { continue }
  $fm = Get-Frontmatter ([System.IO.File]::ReadAllText($t.FullName, $utf8))
  $tp = if ($fm) { $fm['tipo'] } else { '' }
  if ($exentTipos -contains $tp) { continue }
  $rel = $t.FullName.Substring($repo.Length + 1).Replace('\', '/')
  Note "$rel : huerfana (ninguna otra nota la enlaza con [[...]])"
}

# --- 5. Resumen ----------------------------------------------------------------
Write-Host ""
if ($script:block -gt 0) {
  Write-Host "== $($script:block) hallazgo(s) BLOQUEA en el grafo de docs. ==" -ForegroundColor Red
  if ($script:warn -gt 0) { Write-Host "   (+$($script:warn) aviso[s] no bloqueante[s].)" -ForegroundColor Yellow }
  if ($Bloquea) { exit 1 }
  Write-Host "   (modo aviso local: no detiene. El CI con -Bloquea si lo hace.)" -ForegroundColor Yellow
  exit 0
}
elseif ($script:warn -gt 0) {
  Write-Host "== $($script:warn) aviso(s) en el grafo de docs (no bloquean). ==" -ForegroundColor Yellow
  exit 0
}
else { Write-Host "== Grafo de docs integro. ==" -ForegroundColor Green; exit 0 }
