@echo off
cd /d "%~dp0"
echo [1/2] Synthesizing synced Cartoon SFX bed...
uv run --with numpy python build_cartoon_sfx.py
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

echo [2/2] Rendering Color Master + Sin City Selective-Neon Master...
uv run --with imageio-ffmpeg --with numpy python assemble_animatic.py --render --sincity
if %ERRORLEVEL% neq 0 (
    echo [!] Render failed with exit code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)
echo [+] Complete: bigbrownbear_animatic_master.mp4 ^& bigbrownbear_animatic_sincity_master.mp4
