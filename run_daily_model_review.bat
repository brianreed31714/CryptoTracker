@echo off
setlocal
cd /d "%~dp0"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set REVIEWDATE=%%i

echo ============================================================
echo CryptoTracker Agentic Daily Review
echo Review date: %REVIEWDATE%
echo ============================================================
echo.

echo [1/4] Building daily review bundle...
python build_daily_review_bundle.py --date %REVIEWDATE%
if errorlevel 1 goto :fail

echo.
echo [2/4] Running model review...
python daily_model_review.py --date %REVIEWDATE%
if errorlevel 1 goto :fail

echo.
echo [3/4] Publishing proposal registry + REVIEW.md...
python proposal_registry.py publish --date %REVIEWDATE%
if errorlevel 1 goto :fail

echo.
echo [4/4] Syncing proposal registry to GitHub...
python sync_proposals_to_git.py --message "Publish CryptoTracker proposals %REVIEWDATE%"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo Daily review complete.
echo ============================================================
echo.
echo GitHub proposal review:
echo   analysis\proposals\REVIEW.md
echo.
echo To approve in ChatGPT, use:
echo   Approve P-YYYYMMDD-NN
echo.
exit /b 0

:fail
echo.
echo ============================================================
echo Agentic daily review FAILED.
echo ============================================================
exit /b 1
