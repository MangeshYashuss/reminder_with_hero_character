Start Up Bat Command 
@echo off

REM Go to the project directory
cd /d "C:\Users\YU0020\Documents\AI Agents\water_reminder"

REM Activate virtual environment
call ".venv\Scripts\activate.bat"

REM Run the Python application
python main.py

REM Keep terminal open if the application crashes
pause
