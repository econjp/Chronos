@echo off
rem Builds TimerDiary.exe from timer_diary_v5.py (needs Python installed once)
python -m pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name TimerDiary timer_diary_v5.py
echo.
echo Done. Your exe is in the dist\ folder: dist\TimerDiary.exe
echo Move it anywhere you like (e.g. C:\Tools\), run it once --
echo it will ask about launching at Windows startup on first run.
pause
