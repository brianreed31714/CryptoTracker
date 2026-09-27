@echo off
cd /d "%~dp0"
echo Starting CryptoTracker Control Center...
echo.
python -m streamlit run cryptotracker_dashboard_v11_8_2.py
pause
