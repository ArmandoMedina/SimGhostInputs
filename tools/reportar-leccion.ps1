#Requires -Version 5
# reportar-leccion.ps1 - el canal de SUBIDA del lazo labs<->Jidoka. El hijo NO
# parchea su maquinaria: reporta la leccion al tracker de Jidoka, Jidoka la arregla
# con su ritual, y el hijo baja la correccion con ./tools/instalar.ps1 -Actualizar.
# Abre el issue 'leccion.md' de Jidoka, prellenado, en el navegador.
#   -Url <base>   base del repo Jidoka (default: el upstream publico)
# Se siembra en cada hijo (motor). Archivo ASCII a proposito, PS 5.1.

param([string]$Url = 'https://github.com/ArmandoMedina/jidoka')

$issue = "$Url/issues/new?template=leccion.md"
Write-Host "== Reportar una leccion a Jidoka (canal de subida del lazo) =="
Write-Host "  Abriendo: $issue"
Write-Host ""
Write-Host "  La leccion SUBE por el issue; Jidoka la arregla con su ritual; tu BAJAS la"
Write-Host "  correccion con ./tools/instalar.ps1 -Destino <este-repo> -Actualizar (desde Jidoka)."
Write-Host "  Regla 2-3: 2-3 usos reales antes de que una leccion se vuelva regla; un solo"
Write-Host "  uso ya vale registrarlo (queda esperando su segundo). Anonimiza (frontera-nda)."
try { Start-Process $issue | Out-Null }
catch { Write-Host "  (no pude abrir el navegador; copia el link de arriba a mano.)" -ForegroundColor Yellow }
