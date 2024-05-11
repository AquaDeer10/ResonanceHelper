@echo off
@REM if .venv not exists, create it
if not exist .venv (
    python -m venv .venv
)

@REM install requirements
.\.venv\Scripts\pip.exe install -r requirements.txt

@REM build
.\.venv\Scripts\pyinstaller.exe -D .\app.py ^
--collect-all paddleocr ^
--collect-all pyclipper ^
--collect-all imghdr ^
--collect-all skimage ^
--collect-all imgaug ^
--collect-all scipy ^
--collect-all lmdb ^
--add-data .\ui\azure.tcl;.\ui ^
--add-data .\ui\theme;.\ui\theme ^
--add-data .\emulator\platform-tools;.\emulator\platform-tools ^
--add-data .\.venv\Lib\site-packages\paddle\libs;.\paddle\libs ^
--add-data .\icon;.\icon ^
--add-data .\ocr\model;.\ocr\model ^
--add-data .\adb.ini;. ^
--icon .\icon\resonance.ico  ^
--name ResonanceHelper ^
--noconsole ^
--noconfirm
