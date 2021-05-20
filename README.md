# KPI
This python script automatically updates a message board with values from Plex using automation, not an API (Unfortunately).
KPI stands for Key Performance Indicator.
There are two main automation modules/libraries in this program: selenium and pyautogui.
Selenium makes up the bulk of the automation. It can only operate on web brower pages that utilize HTML as it navigates
by HTML elements. Selenium works in the background so a user could still use the computer for other tasks while selenium
is running. However, this is negated by pyautogui. There are some parts of the overall procedure that selenium cannot 
perform as it cannot use HTML to access it. Pyautogui works by emulating human actions such a raw key presses and mouse
clicks. The drawback is that pyautogui performs these actions as if another human is using the computer. The cursor will
move by itself when something is clicked on. Whatever the program is interacting with does have to be in the forefront
of the screen. Since this program uses pyautogui for mouse clicks every minute, whichever computer is used to execute 
this script cannot by used for anything else at running time. Usage during running time will most likely disrupt the
program.

Versions of python and installed modules:
- python 3.7.8
- PyAutoGUI 0.9.52
- selenium 3.141.0
- ChromeDriver 80.0.3987.106
- Visual Studio 16.9.4
- numpy 1.19.5

Requirements:
- Plex login for Wanco
- The correct .ini file (example found in this repository)
- Ethernet cable connection to an active message board

Abbreviations:
Message Board window = MBw,
Plex window = Pw

There are three phases to this script: Setup, Update, Restart.
Setup will happen first, and then Update will happen.
Restart is only entered if an unhandled error occurs in the Setup or Update phase. After the Restart phase, the Setup and Update phase will occur as normal.

Update 11/23/2020: I'm waiting on test Plex credentials so I can take my own out.

Update 12/4/2020: I now have generic Plex credentials.

Update 12/18/2020: Back to my credentials since the generic account got nerfed in terms of what pages it can access. There are 
plans for this program to be used soon. However, there's been issues with getting the board to work on 3x4 panels instead
of the 3x5 I've been working with.

Update 12/22/2020: Although the program interacts with the MBw every minute, the former occassionally asks the user
roughly every half hour to sign back in with the admin/administrator credentials. In this case, a person will have
to type in the credentials. I'm assuming that failing to do so before the next update will prompt a timeout error
and the program will restart. Even though this restart would "fix" everything, all inactivity progress would be lost.
In addition, deploying a program that will raise an error every half hour doesn't sound good.

Update 12/23/2020: It seems that the alert is so special that when it shows up, the program stops at its current line
and freezes up. This has prevented many solutions such as alert_is_present, action chains, and pyautogui. I did find
one exception to this though. Triggering a login prompt via selenium will result in the program freezing up and 
rendering the rest of the execution null. However, triggering a login prompt via manual mouse clicks doesn't freeze
the program, allowing for pyautogui to log in again. The program updates the board every minute; now, it also logs
out and logs back in between those minutes to refresh activity.

Update 12/29/2020: An updated copy of the original program has been fully adapted for a 3x4 board. This new program
also requires the use of an updated .ini file. In addition, I'm thinking about changing the text color to blue or
white if the line meets its quota. This way, the text won't turn red despite the quota being met.

Update 12/30/2020: When a line has a quota and has met it, the text color will turn blue. This signals that a line
has achieved their target amount and prevents the text from turning red out of inactivity. Speaking of inactivity, 
there's an idea of pausing a line when they're on break. The only thing that'd happen for sure during a break is
the line's inactivity counter ceasing to increment. During this time, I could also make the text color turn into
one of the two unused colors: amber and white. Or what if I change the total to say "On Break"? I think the latter
is a better idea since it conveys the message better and too many colors can get confusing. This project is gonna
take a physical form soon.

Update 1/8/2021: There a third python file in the repository called Plex2Board(WithBreak) that's based off of the
Plex2Board3x4 file. While the latter is a program to print information from Plex to a message board, Plex2Board(WithBreak)
is that with a feature to stop the inactivity counter for separate lines when they go on break. The break times 
for lines are a new section of the .ini file.

Update 2/19/2021: A new warning appears alongside the usual (and multiple) "handshake failed" warning. This new warning
happens once or twice a run and it mentions how the "bluetooth adapter failed". Akin to the handshake warning, the 
bluetooth warning can also be ignored.

Update 2/26/2021: The file, 'Plex2Board(WithBreak)', has essentially been assimulated into 'Plex2Board3x4'. Thus,
the former was deleted.

Update 4/20/2021: The section that slected "Production History" is now more universal. Instead of using selenium to
press the down arrow key and enter to select production history, pyautogui will search for the image. This means that 
the user must switch between the MBw and Pw a couple of times. First, the MBw must be in front to allow the program to
login. Second, the Pw must be in front to allow production history to be selected (this comes after Mbw is logged in).
Last, switch MBw back to the front for the rest of the program's operation.

Update 4/30/2021: A new DCU board was hooked up to my computer, so I'm no longer using the old board. This is a huge change,
because now I have to refactor almost all of the code that's associated with the board. Functionality wise, the new board
can do everything the old one could. However, the new web broswer interface doesn't have an option to change text color.
That option is only available on the touchpad. Other differences are minor. First, creating a new message doesn't overwrite
the old message in the editor, so I have to manually flush that out everytime the program starts. Sure, the program is 
supposed to blank the board when it ends properly, but this could be a problem if the program restarts and the old message
persists. Second, clicking options has a longer average wait time. Third, alignment changing is now per page instead of per
line. Fourth, speaking of pages, they're all on separate web pages so no more editing all of them at once. Fifth, when
modifying a page, I have to rewrite everything now since the current message isn't in text form after activation. Sixth,
most of the "find element and click" statements are now nonapplicable since every button has a dot label instead of their
advertised option. This means that every "main" button has different id's and name's and saying "find and click" the "main"
button no longer works. Last, the web interface is noticeably slower than the old interface. Clicking a button may induce
a slight lag/delay in the executed action. This isn't enough to stop the program or break it, but board set up and updating,
on average, takes a bit longer. 

5/18/2021: Today I tried to run the the refactored program all day to see if it truly can performe the same functions as 
the older version. However, there was a major problem with the web inteface. Occasionally, the web interface will lose its
connection to the message board, resulting in a page not found or "empty_response" message to appear on the web page. 
After contecting Richard O'Mally, even he doesn't know what the cause for this is. At this point, we're waiting for a
response from the software team on how to fix this issue. If left alone, the web interface would induce time out errors
at random intervals. Although the program can restart itself in the case of general errors, it's preferrable that it
doesn't do that since that's an indication of unstability. Testing the program is still underway, but time out errors
will be attributed to the shaky web interface connection if the page is down.

Setup Phase:
The script will attempt to locate chromedriver.exe on the computer. Once found, it'll use chromedriver.exe's path and selenium to create 
two webdrivers, driver and remote, that will utilize google chrome. Main() is called while driver and remote are being passed, too.
configparser is used to read the contents of an .ini file, which is in the same directory as the script, into a variable: config.
setup_board() is called with driver and setup_plex() is called with remote. setup_board() uses driver to open a chrome window with the
software to operate the message board. MBw requires login credentials; however, the credentials are entered into an embedded part of the
page. This means selenium cannot reach it, but PyAutoGUI can. Though, the thing about PyAutoGUI is that it's manual automation.
PyAutoGUI will take control of the mouse and it will only interact with windows on the front layer. What this means is that
if the MBw isn't the front most window, the script will attempt to enter the credentials in the wrong location. setup_plex() uses remote
to open a chrome window to operate Plex. The script will navigate to the Production History page on Plex. Finally, the program will
create a new message on the MBw that consist of the current time, line name, and how many trailers they have dropped (out of a quota
if applicable). There will be one "page" for each line specified in the .ini file. 

Update Phase:
In this phase, the program will stay in the function, update_board(), until completion. The board message and its faces will update
every minute due to the time display. Every minute, not only will the program update the current time, it'll also look at each line's
Production History information to check if the amount of trailers dropped increased. In addition, the program keeps track of the amount
of time a line has spent "idle". In the .ini file, each line has an "inactivity" value. Every time the board gets updated and a line's
trailer amount hasn't increased, a separate counter increments. When this counter equals the line's inactivity value, a question mark
is appended to the bottom row. When the line's trailer amount increases, counter is reset to zero and the question mark is removed. It is
In addition, if a line has met their quota, it can no longer be marked with ?. The program will stop when the  current time equals the 
overtime closing time: 4:30 pm. At this point, the program will clear the board, bring MBw back to the main menu, 
and quit both drivers. Before inactivity is incremented for a line, the program will check if the line is on break or not. If not,
inactivity is incremented. If they're on break, inactivity is stalled. The other service this check provides is toggling breaks when
the current time matches one in the .ini file. When a line is on break, an aterisk star * will appear next to the time.

Restart Phase:
This phase only occurs if an error prohibits the script's progress. Every function in the program is called, one way or another, through
main(). This means that any error that occurs will result in the brief exit out of main(). Thus, the call to main() is placed inside
a try block. Should an error (that's uncovered by other try/except blocks inside other functions) happen, main's try block skips
all remaining inner statements and enters the except block. This block simply prints a message stating the program is restarting. Next,
the finally block will quit both drivers to close the windows and free up space in memory. The try/excpet/finally blocks are all in a
while loop. The program will always restart unless the try block fully executes all of its statements; this includes the last statement,
the one that sets the conditions to break the while loop.

3x5 board: 3 rows, 5 light panels in a row, 8 character limit per row with current font (05x07 Fixed Spacing)

3x4 board: 3 rows, 4 light panels in a row, possible 6 character limit per row given that one character is 5 bulbs wides with the current font (05x07 Fixed Spacing)
The only font that would increase the character limit per row is 04x05 Prop Spacing. The downside is that the 05 makes the text much smaller than the 07. This means,
the text might be difficult to see from a distance.
