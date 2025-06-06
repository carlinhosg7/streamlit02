@echo off
REM ATENÇÃO: esse script assume que você tem Python instalado e Git configurado

echo =============================================
echo 🔁 Compactando arquivos CSV para CSV.GZ...
echo =============================================

REM Executa o script Python interno
python compactar_csvs.py

if errorlevel 1 (
    echo ❌ Erro ao compactar CSVs. Verifique o script Python.
    pause
    exit /b
)

echo =============================================
echo 🚀 Subindo para o GitHub...
echo =============================================

git add DADOS_PREDITIVA_*.csv.gz
git commit -m "Compactação real dos CSVs para .csv.gz"
git push

echo =============================================
echo ✅ Processo finalizado com sucesso!
pause
