@echo off
:: ============================================================
:: build.bat — Script de build do FolderMonitor
:: Gera o ícone .ico e compila o executável com PyInstaller
:: ============================================================

title FolderMonitor — Build

echo.
echo ============================================================
echo   FolderMonitor — Gerando executavel...
echo ============================================================
echo.

:: 1. Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.11+ e tente novamente.
    pause
    exit /b 1
)

:: 2. Instalar dependencias
echo [1/4] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo       OK

:: 3. Gerar icone .ico
echo [2/4] Gerando icone...
python generate_icon.py
if errorlevel 1 (
    echo [AVISO] Falha ao gerar icone. Continuando sem icone personalizado.
) else (
    echo       OK
)

:: 4. Limpar builds anteriores
echo [3/4] Limpando builds anteriores...
if exist "dist\FolderMonitor.exe" del /f /q "dist\FolderMonitor.exe"
if exist "build" rmdir /s /q "build"
echo       OK

:: 5. Compilar com PyInstaller
echo [4/4] Compilando com PyInstaller (aguarde)...
pyinstaller main.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo [ERRO] Falha na compilacao. Veja o log acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build concluido com sucesso!
echo   Executavel: dist\FolderMonitor.exe
echo ============================================================
echo.

:: Perguntar se quer abrir a pasta dist
set /p open_dist="Abrir pasta dist? [S/n]: "
if /i "%open_dist%"=="n" goto :end
explorer dist

:end
pause
