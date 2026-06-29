# setup.ps1 - instala todas las dependencias de SimGhostInputs en Windows
# Uso: powershell -ExecutionPolicy Bypass -File setup.ps1
# Parametros opcionales:
#   -Full       instala dependencias Python completas (openpyxl + Pillow + matplotlib)
#   -SkipSystem omite instalacion de herramientas del sistema (ffmpeg, gh)
#   -Yes        modo desatendido: responde "si" a todas las confirmaciones, sin Read-Host
#               (para CI / pruebas en VM limpia). Combina con -SkipSystem para evitar las apps
#               grandes (VLC, Kdenlive). En -Yes no se relanza una terminal nueva tras instalar
#               Python (inservible en headless): se resuelve la ruta de Python en la misma sesion.
param(
    [switch]$Full,
    [switch]$SkipSystem,
    [switch]$Yes,
    [switch]$Relaunched   # uso interno: marca que ya se reabrio tras instalar Python (anti-bucle)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Msg) Write-Host "`n==> $Msg" -ForegroundColor Cyan }
function Write-OK   { param([string]$Msg) Write-Host "    OK: $Msg" -ForegroundColor Green }
function Write-Skip { param([string]$Msg) Write-Host "    --: $Msg" -ForegroundColor DarkGray }
function Write-Warn { param([string]$Msg) Write-Host "    !! $Msg" -ForegroundColor Yellow }
# Confirmacion que respeta el modo desatendido: con -Yes asume "si" sin preguntar.
function Confirm-Action {
    param([string]$Prompt)
    if ($Yes) { Write-Host "$Prompt s (auto -Yes)" -ForegroundColor DarkGray; return $true }
    return ((Read-Host $Prompt) -eq "s")
}

# -----------------------------------------------------------------------
# 1. Python
# -----------------------------------------------------------------------
Write-Step "Verificando Python"
# Windows 11 trae un stub de python.exe en WindowsApps (alias de la Microsoft Store) que NO es
# Python real: aparece en Get-Command, pero al ejecutarlo abre la Store o falla. Si no se ignora,
# el script creeria que Python ya esta instalado y reventaria mas adelante al llamar pip.
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd -and ($pythonCmd.Source -notmatch 'WindowsApps')) {
    Write-OK (python --version 2>&1)
} else {
    if ($pythonCmd) { Write-Warn "Ignorando el stub de Python de la Microsoft Store (WindowsApps); no es Python real." }
    Write-Warn "Python no encontrado."
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Error "Tampoco hay winget. Instala Python 3.10+ a mano desde https://python.org (marca 'Add Python to PATH') y vuelve a correr setup.ps1."
        exit 1
    }
    if (-not (Confirm-Action "    Instalar Python 3.12 via winget ahora? (s/n)")) {
        Write-Error "Python es obligatorio. Instalalo desde https://python.org y vuelve a correr setup.ps1."
        exit 1
    }
    # --source winget es obligatorio: si la Microsoft Store tambien expone el paquete, winget
    # aborta con "multiple sources found" (exit -1978335138) al no saber cual usar.
    winget install Python.Python.3.12 --source winget --accept-source-agreements --accept-package-agreements
    # winget actualiza el PATH en el registro, pero NO en esta sesion ya abierta.
    # Se intenta refrescar desde el registro (Machine + User).
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    # En headless (PowerShell Direct / SSH / CI) ni refrescar el registro basta: hay que LOCALIZAR
    # el python REAL recien instalado y anteponerlo al PATH. Se IGNORA el stub de WindowsApps (que
    # resuelve 'python' pero no es Python) y se cubre user y machine con version variable
    # (Python312, Python313...) globeando, en vez de rutas fijas que winget puede no usar.
    $pyExe = $null
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and ($cmd.Source -notmatch 'WindowsApps')) {
        $pyExe = $cmd.Source
    } else {
        foreach ($base in @("$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles", "${env:ProgramFiles(x86)}")) {
            if ($base -and (Test-Path $base)) {
                foreach ($d in (Get-ChildItem -Path $base -Directory -Filter "Python3*" -ErrorAction SilentlyContinue)) {
                    $maybe = Join-Path $d.FullName "python.exe"
                    if (Test-Path $maybe) { $pyExe = $maybe; break }
                }
            }
            if ($pyExe) { break }
        }
    }
    if ($pyExe) {
        $pyDir = Split-Path -Parent $pyExe
        $env:Path = "$pyDir;$pyDir\Scripts;$env:Path"
    }

    $cmd2 = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd2 -and ($cmd2.Source -notmatch 'WindowsApps')) {
        Write-OK ("Python instalado: " + (python --version 2>&1))
    } elseif ($Relaunched -or $Yes) {
        # No relanzamos una terminal nueva en modo desatendido (-Yes) ni si ya se reintento una vez
        # (anti-bucle): en headless/CI una ventana nueva no sirve. Mejor fallar claro.
        Write-Error "Python se instalo pero no se encontro su ejecutable. Abre una terminal nueva (o reinicia) y vuelve a correr setup.ps1."
        exit 1
    } else {
        # Una terminal NUEVA si hereda el PATH actualizado del registro. Abrimos otra,
        # que re-corre este mismo setup con -Relaunched, y cerramos esta.
        Write-Warn "Python instalado. Abriendo una terminal nueva con el PATH actualizado..."
        $argList = @("-ExecutionPolicy", "Bypass", "-NoExit", "-File", "`"$PSCommandPath`"", "-Relaunched")
        if ($Full)       { $argList += "-Full" }
        if ($SkipSystem) { $argList += "-SkipSystem" }
        Start-Process powershell -ArgumentList $argList
        exit 0
    }
}

# -----------------------------------------------------------------------
# 2. Paquete fantasma-inputs
# -----------------------------------------------------------------------
Write-Step "Instalando fantasma-inputs"
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($Full) {
    Write-Host "    Modo --Full: openpyxl + Pillow + matplotlib"
    pip install -e "$script_dir[full]" --quiet
} else {
    Write-Host "    Modo basico (agregar -Full para graficas y overlay)"
    pip install -e "$script_dir" --quiet
}
Write-OK "fantasma-inputs instalado"

# -----------------------------------------------------------------------
# 3. Dependencias Python opcionales (si no se eligio --Full)
# -----------------------------------------------------------------------
if (-not $Full) {
    Write-Step "Instalando dependencias opcionales"

    # Nota: los comandos nativos (python) reportan fallo via $LASTEXITCODE, NO lanzan
    # excepcion que atrape un try/catch. Por eso se comprueba el codigo de salida a mano.

    # openpyxl: para leer .xlsx exportados de MoTeC i2
    python -c "import openpyxl" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Skip "openpyxl ya instalado"
    } else {
        pip install openpyxl --quiet
        Write-OK "openpyxl instalado  (leer .xlsx)"
    }

    # Pillow: requerido por 'fantasma overlay'
    python -c "from PIL import Image" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Skip "Pillow ya instalado"
    } else {
        pip install "Pillow>=10" --quiet
        Write-OK "Pillow instalado  (fantasma overlay)"
    }

    # matplotlib: opcional, para 'fantasma compare' con graficas
    python -c "import matplotlib" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Skip "matplotlib ya instalado"
    } else {
        if (Confirm-Action "    Instalar matplotlib para graficas ghost? (s/n)") {
            pip install "matplotlib>=3.7" --quiet
            Write-OK "matplotlib instalado  (graficas ghost)"
        } else {
            Write-Skip "matplotlib omitido  (fantasma compare funcionara sin graficas)"
        }
    }
}

# -----------------------------------------------------------------------
# 4. Herramientas del sistema
# -----------------------------------------------------------------------
if ($SkipSystem) {
    Write-Skip "Herramientas del sistema omitidas (-SkipSystem)"
} else {
    Write-Step "Verificando herramientas del sistema"

    # ffmpeg: necesario para codificar el video de overlay (.webm / .mov)
    # sin el, 'fantasma overlay' genera frames PNG igualmente
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Skip "ffmpeg ya instalado  ($(ffmpeg -version 2>&1 | Select-Object -First 1))"
    } else {
        Write-Warn "ffmpeg no encontrado - el overlay generara frames PNG en lugar de video"
        if (Confirm-Action "    Instalar ffmpeg via winget? (s/n)") {
            winget install Gyan.FFmpeg --source winget --accept-source-agreements --accept-package-agreements
            Write-OK "ffmpeg instalado  (reinicia la terminal para que quede en PATH)"
        } else {
            Write-Warn "Sin ffmpeg: 'fantasma overlay --format webm/prores' queda como PNG"
        }
    }

    # gh: GitHub CLI, para subir el repositorio
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        Write-Skip "GitHub CLI ya instalado"
    } else {
        if (Confirm-Action "    Instalar GitHub CLI (gh) via winget? (s/n)") {
            winget install GitHub.cli --source winget --accept-source-agreements --accept-package-agreements
            Write-OK "gh instalado  (autenticate con: gh auth login)"
        } else {
            Write-Skip "gh omitido  (puedes subir el repo manualmente desde github.com/new)"
        }
    }

    # VLC: para previsualizar overlay.webm con canal alfa
    $vlcPath = "C:\Program Files\VideoLAN\VLC\vlc.exe"
    if ((Get-Command vlc -ErrorAction SilentlyContinue) -or (Test-Path $vlcPath)) {
        Write-Skip "VLC ya instalado"
    } else {
        if (Confirm-Action "    Instalar VLC (previsualizar overlay.webm con alfa)? (s/n)") {
            winget install VideoLAN.VLC --source winget --accept-source-agreements --accept-package-agreements
            Write-OK "VLC instalado"
        } else {
            Write-Skip "VLC omitido"
        }
    }

    # Kdenlive: editor open source para sincronizar HUD con la grabacion
    $kdenlivePath = "C:\Program Files\kdenlive\bin\kdenlive.exe"
    if ((Get-Command kdenlive -ErrorAction SilentlyContinue) -or (Test-Path $kdenlivePath)) {
        Write-Skip "Kdenlive ya instalado"
    } else {
        if (Confirm-Action "    Instalar Kdenlive (editor open source para sincronizar el HUD con tu grabacion)? (s/n)") {
            winget install KDE.Kdenlive --source winget --accept-source-agreements --accept-package-agreements
            Write-OK "Kdenlive instalado"
        } else {
            Write-Skip "Kdenlive omitido  (otras opciones: DaVinci Resolve, Premiere)"
        }
    }
}

# -----------------------------------------------------------------------
# 5. Resumen
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  SimGhostInputs listo." -ForegroundColor Cyan
Write-Host ""
Write-Host "  fantasma laps mi_export.csv"
Write-Host "  fantasma detect mi_export.csv -o salida/"
Write-Host "  fantasma compare --reference ref.csv --driver yo.csv -o salida/"
Write-Host "  fantasma overlay --reference ref.csv --driver yo.csv --format webm -o salida/"
Write-Host ""
Write-Host "  Mas info: https://github.com/ArmandoMedina/SimGhostInputs"
Write-Host "======================================================" -ForegroundColor Cyan
