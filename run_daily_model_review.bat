@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo CryptoTracker Daily Model Review
echo ============================================================
echo.

python build_daily_review_bundle.py
if errorlevel 1 (
  echo.
  echo Bundle build FAILED.
  pause
  exit /b 1
)

echo.
python daily_model_review.py
if errorlevel 1 (
  echo.
  echo Daily model review FAILED.
  pause
  exit /b 1
)

echo.
echo Review complete.
echo See analysis\daily\YYYY-MM-DD\daily_model_review.md
echo.
pause
