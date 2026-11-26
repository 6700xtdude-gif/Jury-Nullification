@echo off
echo Building Big Brown Bear Animatic Cut...
:: Check for ffmpeg
where ffmpeg >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] ffmpeg not found in PATH. Install via: winget install Gyan.FFmpeg
    pause
    exit /b 1
)

ffmpeg -y -i "D:\Shared_3D2A\BigBrownBear\Recording (6).m4a" -c:a aac -b:a 192k "D:\Shared_3D2A\BigBrownBear\master_audio.wav"
echo Audio extracted.
pause
