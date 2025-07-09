@echo off
setlocal

echo Menjalankan aplikasi Flask dari virtual environment...

:: Jalankan Flask di jendela baru dan simpan PID (Process ID)
start "FlaskApp" cmd /c ".venv\Scripts\python.exe app.py"
timeout /t 3 >nul

:: Buka Microsoft Edge
start msedge http://127.0.0.1:5000

:loop
set /p input=Tekan [Q] lalu [Enter] untuk menghentikan server: 
if /i "%input%"=="Q" goto stop
goto loop

:stop
echo.
echo Menutup server Flask...

:: Bunuh proses Flask (semua python.exe — hati-hati jika ada proses Python lain)
taskkill /f /im python.exe >nul 2>&1

echo Server dimatikan.
pause
endlocal
