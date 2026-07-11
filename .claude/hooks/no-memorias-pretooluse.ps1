# no-memorias-pretooluse.ps1 - PreToolUse hook. Bloquea escrituras a la memoria
# persistente de Claude: la regla es "nada de memorias, todo al repo". Jidoka
# corre su propio Andon (dogfooding): el repo de la metodologia hace cumplir su
# propia doctrina. La regla se cablea como gate porque repetirla en prosa se
# olvida; el punto de control vive FUERA del LLM (la tesis de Jidoka).
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

$razon = "Nada de memorias: todo al repo (disparo anti-memoria de Jidoka). Lo que ibas a guardar tiene un " +
         "lugar con dueno: estado en vuelo o pendientes -> HANDOFF.md; una decision y su porque -> " +
         "docs/decisions/ (un ADR, y listalo en el indice); doctrina o hecho del dominio -> doctrina/; y si es " +
         "una regla accionable nueva, ademas su forma compilada -> kit/.jidoka/disparos/. Esta regla se cablea " +
         "porque en prosa fallo 4 veces en el laboratorio de campo antes de volverse hook (ADR 0003 de la " +
         "doctrina). Si de verdad es una preferencia personal trans-repo del usuario, pidele confirmacion " +
         "explicita antes."
$out = @{
  hookSpecificOutput = @{
    hookEventName            = 'PreToolUse'
    permissionDecision       = 'deny'
    permissionDecisionReason = $razon
  }
}
$out | ConvertTo-Json -Compress -Depth 5
exit 0
