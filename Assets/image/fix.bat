@echo off
echo ImageMagick fix libpng warning: iCCP: Not recognizing known sRGB profile ......
echo Search PNG in subdirs and process ...
set fn=D:\ImageMagick-7.0.10-10-portable-Q16-x64\convert.exe
for /f "tokens=*" %%i in ('dir/s/b *.png') do "%fn%" "%%i" -strip "%%i"
pause