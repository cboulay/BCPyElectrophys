#! ../BCI2000/prog/BCI2000Shell
@cls & ..\BCI2000\prog\BCI2000Shell %0 %* #! && exit /b 0 || exit /b 1\n
Change directory $BCI2000LAUNCHDIR
Show window; Set title ${Extract file base $0}
Reset system
Startup system localhost
Start executable SignalGenerator --local
Start executable SpectralSignalProcessing --local
Start executable PythonApplication --local --PythonAppClassFile=..\..\BCPyElectrophys\TemplateApplication.py --PythonAppWD=..\..\BCPyElectrophys
Wait for Connected
Load parameterfile "../../BCPyElectrophys/test.prm"