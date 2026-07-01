# no-memorias-pretooluse.ps1 - PreToolUse hook (homologado del starter v0.5.0,
# ADR 0019). Bloquea escrituras a la memoria persistente de Claude durante
# sesiones de este repo: la regla es "nada de memorias, todo al repo" y se hizo
# cumplir con hook porque repetirla no funciono (4 veces en las sesiones reales
# de ESTE repo; y hasta planeando esta regla la IA escribio una memoria).
#
# Que bloquea: Write/Edit cuyo file_path caiga en una carpeta de memoria de
# Claude (~/.claude/projects/<slug>/memory/). El mensaje ensena a donde va
# cada cosa. Se cablea en .claude/settings.json (matcher Write|Edit).
# Archivo ASCII a proposito (PS 5.1).

$ErrorActionPreference = 'SilentlyContinue'

$raw = [Console]::In.ReadToEnd()
try { $inp = $raw | ConvertFrom-Json } catch { exit 0 }
if (-not $inp) { exit 0 }
$path = $inp.tool_input.file_path
if (-not $path) { exit 0 }

# Normalizar separadores para comparar.
$norm = $path.Replace('\', '/')
if ($norm -notmatch '/\.claude/projects/[^/]+/memory/') { exit 0 }

$razon = "Nada de memorias: todo al repo (ADR 0019). Lo que ibas a guardar tiene un lugar con dueno: " +
         "estado en vuelo o pendientes -> HANDOFF.md; una decision y su porque -> docs/decisions/ (ADR); " +
         "hechos de producto o del dominio -> product/; recursos externos -> docs/recursos-del-proyecto.md; " +
         "lecciones de entorno -> docs/entorno-windows-powershell51.md. " +
         "Si de verdad es una preferencia personal trans-repo del usuario, pidele confirmacion explicita antes."
$out = @{
  hookSpecificOutput = @{
    hookEventName            = 'PreToolUse'
    permissionDecision       = 'deny'
    permissionDecisionReason = $razon
  }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
