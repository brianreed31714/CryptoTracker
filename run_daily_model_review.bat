@echo off
setlocal
cd /d "%~dp0"

rem At 18:05 Pacific the current 24/7 crypto calendar day is still incomplete.
rem Review the prior *completed* Pacific day. An explicit date remains available
rem for a controlled historical rerun; this batch never sends swaps or restarts.
if not "%~1"=="" (
  set REVIEWDATE=%~1
) else (
  for /f %%i in ('python -m infrastructure.completed_crypto_day') do set REVIEWDATE=%%i
)
if not defined REVIEWDATE goto :fail

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
rem Read-only one-shot Windows evidence; cannot change review success.
python -m infrastructure.windows_activation_attestation --notify
if errorlevel 1 echo CryptoTracker Windows attestation unavailable; model review still complete.
exit /b 0

:fail
echo.
echo ============================================================
echo Agentic daily review FAILED.
echo ============================================================
exit /b 1
