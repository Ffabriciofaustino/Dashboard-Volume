@echo off
cd /d "C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto Volume"

echo ================================
echo ATUALIZANDO DADOS...
echo ================================

python volume_BH.py

echo ================================
echo ABRINDO DASHBOARD...
echo ================================

streamlit run dashboard.py

pause