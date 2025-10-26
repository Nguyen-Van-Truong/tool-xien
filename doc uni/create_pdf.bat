@echo off
echo Converting HTML to PDF...

REM Try different Edge locations
set "edge1=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
set "edge2=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
set "chrome1=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
set "chrome2=C:\Program Files\Google\Chrome\Application\chrome.exe"

REM Get full path to HTML file
set "htmlfile=%cd%\Flinders_University_Confirmation_of_Enrolment_PDF_Ready.html"
set "pdffile=%cd%\Flinders_University_Confirmation_of_Enrolment.pdf"

REM Try Edge first
if exist "%edge1%" (
    echo Using Edge (x86)...
    "%edge1%" --headless --disable-gpu --print-to-pdf="%pdffile%" "%htmlfile%"
    goto :done
)

if exist "%edge2%" (
    echo Using Edge (x64)...
    "%edge2%" --headless --disable-gpu --print-to-pdf="%pdffile%" "%htmlfile%"
    goto :done
)

REM Try Chrome if Edge not found
if exist "%chrome1%" (
    echo Using Chrome (x86)...
    "%chrome1%" --headless --disable-gpu --print-to-pdf="%pdffile%" "%htmlfile%"
    goto :done
)

if exist "%chrome2%" (
    echo Using Chrome (x64)...
    "%chrome2%" --headless --disable-gpu --print-to-pdf="%pdffile%" "%htmlfile%"
    goto :done
)

echo Error: No suitable browser found!
echo Please install Microsoft Edge or Google Chrome.
pause
goto :end

:done
if exist "%pdffile%" (
    echo.
    echo SUCCESS: PDF created successfully!
    echo File location: %pdffile%
) else (
    echo.
    echo ERROR: PDF creation failed!
)

:end
pause 