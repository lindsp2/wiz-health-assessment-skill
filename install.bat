@echo off
setlocal
echo =======================================================
echo      WIZ HEALTH ASSESSMENT & SKILLS INSTALLER (Windows)
echo =======================================================

:: Check for python / py
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=python
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PY_CMD=py
    ) else (
        echo [!] Python is required but was not found in your PATH.
        echo     Please install Python 3.9+ from https://python.org and check 'Add Python to PATH'.
        pause
        exit /b 1
    )
)

echo [*] Checking Python dependencies...
%PY_CMD% -m pip install -r requirements.txt --quiet

echo [*] Running skills installer...
%PY_CMD% scripts\install_skills.py

endlocal
