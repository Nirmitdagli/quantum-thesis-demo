@echo off
REM =====================================================================
REM  Hybrid CPU+GPU+QPU Cybersecurity Simulator - one-click launcher
REM  Double-click this file to execute the full 17-task pipeline and
REM  regenerate all 6 publication-quality diagrams.
REM =====================================================================

title Hybrid Quantum-Classical AI Simulator

REM Jump to this script's own directory so relative paths work
cd /d "%~dp0"

REM Force UTF-8 so box-drawing characters in the simulator output render
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo.
echo ======================================================================
echo   HYBRID CPU + GPU + QPU CYBERSECURITY SIMULATOR
echo   QSVM anomaly detection  +  QAOA segmentation  +  Grover search
echo ======================================================================
echo.
echo Working directory: %CD%
echo.

REM Try `py` launcher first (standard on Windows), then fall back to `python`
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY=py -3"
) else (
    set "PY=python"
)

echo Using interpreter: %PY%
echo.
echo Launching hybrid pipeline (this takes ~2 seconds)...
echo.

%PY% -m hybrid_simulation.run_hybrid
set "EXITCODE=%ERRORLEVEL%"

echo.
echo ======================================================================
if %EXITCODE%==0 (
    echo   SUCCESS. Outputs written to:
    echo     hybrid_simulation\output\hybrid_summary.txt
    echo     hybrid_simulation\output\hybrid_pipeline_results.csv
    echo     hybrid_simulation\output\plots\  ^(6 diagrams^)
    echo.
    echo   Opening plots folder...
    start "" "hybrid_simulation\output\plots"
) else (
    echo   FAILED with exit code %EXITCODE%.
    echo   Common fixes:
    echo     1. Install dependencies:  %PY% -m pip install qiskit qiskit-aer scikit-learn networkx matplotlib numpy
    echo     2. Verify Python is on PATH
)
echo ======================================================================
echo.
pause
