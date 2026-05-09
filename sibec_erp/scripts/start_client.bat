@echo off
cd /d %~dp0\..
py -3 -c "import sys" >nul 2>&1
if errorlevel 1 (
  echo Python 3 est requis pour lancer le client.
  echo Installez Python puis relancez ce script.
  pause
  exit /b 1
)

py -3 client.py
if errorlevel 1 (
  echo Echec du lancement du client ERP.
  pause
  exit /b 1
)
