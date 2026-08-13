$ErrorActionPreference = "Stop"

$raizProyecto = $PSScriptRoot
$pythonProyecto = Join-Path $raizProyecto ".venv\Scripts\python.exe"
$salidaAplicacion = Join-Path $raizProyecto "dist\NEPOS\NEPOS.exe"
$salidaConfigurador = Join-Path $raizProyecto "dist\Configurar_NEPOS.exe"

if ($env:OS -ne "Windows_NT") {
    throw "Los ejecutables de NEPOS deben compilarse en Windows."
}

if (-not (Test-Path $pythonProyecto)) {
    throw "No existe .venv. Creala con: py -3.13 -m venv .venv"
}

Push-Location $raizProyecto
try {
    Write-Host "Instalando dependencias de compilacion..." -ForegroundColor Cyan
    & $pythonProyecto -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron instalar las dependencias de compilacion."
    }

    Write-Host "Compilando NEPOS..." -ForegroundColor Cyan
    & $pythonProyecto -m PyInstaller --clean --noconfirm NEPOS.spec
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo la compilacion de NEPOS.exe."
    }

    Write-Host "Compilando el configurador..." -ForegroundColor Cyan
    & $pythonProyecto -m PyInstaller --clean --noconfirm NEPOS_Config.spec
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo la compilacion de Configurar_NEPOS.exe."
    }

    if (-not (Test-Path $salidaAplicacion)) {
        throw "No se genero $salidaAplicacion"
    }
    if (-not (Test-Path $salidaConfigurador)) {
        throw "No se genero $salidaConfigurador"
    }

    Write-Host "Ejecutables generados correctamente:" -ForegroundColor Green
    Write-Host "  $salidaAplicacion"
    Write-Host "  $salidaConfigurador"

    $rutasInno = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    $compiladorInno = $rutasInno |
        Where-Object { $_ -and (Test-Path $_) } |
        Select-Object -First 1

    if ($compiladorInno) {
        Write-Host "Compilando instalador..." -ForegroundColor Cyan
        & $compiladorInno (Join-Path $raizProyecto "instalador\NEPOS.iss")
        if ($LASTEXITCODE -ne 0) {
            throw "Fallo la compilacion del instalador de Inno Setup."
        }
        Write-Host "Instalador generado en dist\instalador." -ForegroundColor Green
    }
    else {
        Write-Warning (
            "Inno Setup 6 no esta instalado. Los ejecutables quedaron listos, " +
            "pero todavia no se genero el instalador."
        )
    }
}
finally {
    Pop-Location
}
