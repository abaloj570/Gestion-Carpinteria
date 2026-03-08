@echo off
title Lanzador Carpinteria Movil
echo Activando entorno virtual...
call venv\Scripts\activate
echo Iniciando servidor de la App...
streamlit run app_movil.py
pause