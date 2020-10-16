# KPI
This python script automatically updates a message board with values from Plex uising automation, not an API (Unfortunately).

Versions of python and installed modules:
python 3.7.8
PyAutoGUI 0.9.52
selenium 3.141.0
ChromeDriver 80.0.3987.106
Visual Studio 16.7.6

Requirements:
Plex login for Wanco
The correct .ini file (example found in this repository)
Ethernet connection to an active message board

Abbreviations:
Message Board window = MBw
Plex window = Pw

There are three phases to this script: Setup, Update, Restart.
Setup will happen first, and then Update will happen.
Restart is only entered if an unhandled error occurs in the Setup or Update phase. After the Restart phase, the Setup and Update phase will occur as normal.

Setup:
The script will attempt to locate chromedriver.exe on the computer. Once found, it'll use chromedriver.exe's path and selenium to create 
two webdrivers, driver and remote, that will utilize google chrome. Main() is called while driver and remote are being passed, too.
configparser is used to read the contents of an .ini file, which is in the same directory as the script, into a variable: config.
setup_board() is called with driver and setup_plex() is called with remote. setup_board() uses driver to open a chrome window with the
software to operate the message board. MBw requires login credentials; however, the credentials are entered into an embedded part of the
page. This means selenium cannot reach it, but PyAutoGUI can. Though, the thing about PyAutoGUI is that it's manual automation.
PyAutoGUI will take control of the mouse and it will only interact with windows on the front layer. What this means is that
if the MBw isn't the front most window, the script will attempt to enter the credentials in the wrong location.
