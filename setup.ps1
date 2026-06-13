# setup.ps1 — instala todas las dependencias de Fantasma Inputs en Windows
# Uso: powershell -ExecutionPolicy Bypass -File setup.ps1
# Parametros opcionales:
#   -Full       instala dependencias Python completas (openpyxl + Pillow + matplotlib)
#   -SkipSystem omite instalacion de herramientas del sistema (ffmpeg, gh)
param(
    [switch]$Full,
    [switch]$SkipSystem
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Msg) Write-Host "`n==> $Msg" -ForegroundColor Cyan }
function Write-OK   { param([string]$Msg) Write-Host "    OK: $Msg" -ForegroundColor Green }
function Write-Skip { param([string]$Msg) Write-Host "    --: $Msg" -ForegroundColor DarkGray }
function Write-Warn { param([string]$Msg) Write-Host "    !! $Msg" -ForegroundColor Yellow }

# -----------------------------------------------------------------------
# 1. Python
# -----------------------------------------------------------------------
Write-Step "Verificando Python"
try {
    $pyver = python --version 2>&1
    Write-OK $pyver
} catch {
    Write-Error "Python no encontrado. Instala Python 3.10+ desde python.org o ejecuta: winget install Python.Python.3.12"
    exit 1
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

    # openpyxl: para leer .xlsx exportados de MoTeC i2
    try {
        python -c "import openpyxl" 2>$null
        Write-Skip "openpyxl ya instalado"
    } catch {
        pip install openpyxl --quiet
        Write-OK "openpyxl instalado  (leer .xlsx)"
    }

    # Pillow: requerido por 'fantasma overlay'
    try {
        python -c "from PIL import Image" 2>$null
        Write-Skip "Pillow ya instalado"
    } catch {
        pip install "Pillow>=10" --quiet
        Write-OK "Pillow instalado  (fantasma overlay)"
    }

    # matplotlib: opcional, para 'fantasma compare' con graficas
    try {
        python -c "import matplotlib" 2>$null
        Write-Skip "matplotlib ya instalado"
    } catch {
        $resp = Read-Host "    Instalar matplotlib para graficas ghost? (s/n)"
        if ($resp -eq "s") {
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
        Write-Warn "ffmpeg no encontrado — el overlay generara frames PNG en lugar de video"
        $resp = Read-Host "    Instalar ffmpeg via winget? (s/n)"
        if ($resp -eq "s") {
            winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
            Write-OK "ffmpeg instalado  (reinicia la terminal para que quede en PATH)"
        } else {
            Write-Warn "Sin ffmpeg: 'fantasma overlay --format webm/prores' queda como PNG"
        }
    }

    # gh: GitHub CLI, para subir el repositorio
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        Write-Skip "GitHub CLI ya instalado"
    } else {
        $resp = Read-Host "    Instalar GitHub CLI (gh) via winget? (s/n)"
        if ($resp -eq "s") {
            winget install GitHub.cli --accept-source-agreements --accept-package-agreements
            Write-OK "gh instalado  (autenticate con: gh auth login)"
        } else {
            Write-Skip "gh omitido  (puedes subir el repo manualmente desde github.com/new)"
        }
    }
}

# -----------------------------------------------------------------------
# 5. Resumen
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Fantasma Inputs listo." -ForegroundColor Cyan
Write-Host ""
Write-Host "  fantasma laps mi_export.csv"
Write-Host "  fantasma detect mi_export.csv -o salida/"
Write-Host "  fantasma compare --reference ref.csv --driver yo.csv -o salida/"
Write-Host "  fantasma overlay --reference ref.csv --driver yo.csv --format webm -o salida/"
Write-Host ""
Write-Host "  Mas info: https://github.com/tu-usuario/fantasma-inputs"
Write-Host "======================================================" -ForegroundColor Cyan
