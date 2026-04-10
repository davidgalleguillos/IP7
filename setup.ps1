# IPv7 Automated Windows Installer
Write-Host "Iniciando instalacion automatica de IPv7..." -ForegroundColor Cyan

# 1. Verificar Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python no esta instalado o no esta en el PATH." -ForegroundColor Red
    exit 1
}

# 2. Crear entorno virtual
if (!(Test-Path venv)) {
    Write-Host "Creando entorno virtual..."
    python -m venv venv
}

# 3. Instalar dependencias
Write-Host "Instalando dependencias desde requirements.txt..."
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\pip install -e .

# 4. Crear acceso directo CLI
$cli_script = "@echo off`nset PYTHONPATH=%PYTHONPATH%;%CD%`n.\venv\Scripts\python.exe %CD%\ipv7\cli.py %*"
$cli_script | Out-File -FilePath ipv7.bat -Encoding ASCII

Write-Host "`n[✓] IPv7 instalado correctamente!" -ForegroundColor Green
Write-Host "Puedes usar '.\ipv7.bat status' para verificar."
Write-Host "Para lanzar la GUI: '.\venv\Scripts\python.exe gui/server.py'"
