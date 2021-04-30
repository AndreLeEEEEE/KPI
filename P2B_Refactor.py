# For a 3x4 board

import pyautogui as auto
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys  # Allows access to non character keys
from selenium.webdriver.common.action_chains import ActionChains
from configparser import ConfigParser  # Needed to read in from .ini files

def find_by(web_driver, attribute, value, click = 0):
    """Interacts with an element by attribute."""
    e_wait = WebDriverWait(web_driver, 10)  # Set explicit wait
    if attribute == "name":
        element = e_wait.until(
            EC.presence_of_element_located((By.NAME, value)))
    elif attribute == "id":
        element = e_wait.until(
            EC.presence_of_element_located((By.ID, value)))

    if click:
        element.click()
    else:
        return element

def get_qty(web_driver, location):
    """Returns the current total dropped by one line."""
    input_box = find_by(web_driver, "id", "flttxtWorkcenter")
    input_box.clear()
    input_box.send_keys(location)
    for i in range(2):
        find_by(web_driver, "id", "SubmitLink", 1)
    try:
        # Finding cur_qty doesn't use the find_by function for two reasons
        # 1. The explicit wait from find_by is unnecessary since the page is already loaded,
        # so the element with the class_name should be visible
        # 2. If the amount of produced units is 0, I'd want to program to know that immediately
        # as opposed to doing the explicit wait. Thus, not using find_by here is faster
        cur_qty = web_driver.find_element_by_class_name("GridSummaryRow")
        cur_qty = re.findall("\d+", cur_qty.text)
    except:  # If the line has currently made nothing, handle the error by manually assigning zero
        cur_qty = ["0"]

    return cur_qty[0]  # Returns a string

def get_time():
    """Returns the current time in regular time."""
    reg_time = time.strftime("%H:%M", time.localtime())  # this is a str '##:##'
    if int(reg_time[:2]) > 12:  # If the hour is past noon
        reg_time = str(int(reg_time[:2])-12) + reg_time[2:]  # Change to regular time
    else:  # If noon or before
        if reg_time[0] == "0":
            reg_time = reg_time[1:]  # Drop the first 0 if present

    return reg_time  # Returns a string

def login():
    """Login into the message board."""
    auto.write("admin")  # Since the username field is already active and embedded, write admin
    auto.write(["tab"])  # Go to the password field
    auto.write("administrator")
    auto.write(["enter"])

def update_board(driver, remote, config):
    """Will update the time and total on the board."""
    # Inner functions
    def update(message, clock, location, break_time):
        """Where all the writing happens for one panel."""
        for go in range(21):  # Move the cursor to the top left of the box
            message.send_keys(Keys.ARROW_LEFT)
        message.send_keys(Keys.ARROW_DOWN)
        message.send_keys(Keys.ARROW_LEFT)  # Maneuver to the right side of the first line
        if break_time[0] == True:  # If on break, go left pass the asterik
            message.send_keys(Keys.ARROW_LEFT)
        for go in range(5):  # Clear everything on this line
            message.send_keys(Keys.BACKSPACE)  # 5 times because longest case could be "12:00"
        message.send_keys(clock)

        for go in range(3):  # Go one line beyond the last line
            message.send_keys(Keys.ARROW_DOWN)
        all_lines = message.text.split()
        if "/" in all_lines[2]:  # Check for quota
            for go in range(3):  # Go to just after the current total if the quota is one digit
                message.send_keys(Keys.ARROW_LEFT)
            temp = all_lines[2].split('/')
            if len(temp[1]) == 2: # If the quota is two digits
                message.send_keys(Keys.ARROW_LEFT)  # Go left one more time
            temp = temp[0]  # Get total
        else:
            message.send_keys(Keys.ARROW_LEFT)  # Go left once to reach end of total
            temp = all_lines[2]  # Get total

        if len(temp) == 2:  # If the current total has two digits
            message.send_keys(Keys.BACKSPACE)  # Backspace one more time
        message.send_keys(Keys.BACKSPACE)  # Always backspace at least once
        message.send_keys(get_qty(remote, location))

    def check_txt_color(index, locations, prev_val, red_mark, inact):
        """Change the text color of a line when necessary."""
        num_drop = get_qty(remote, locations[index])  # A string variable
        quota = config.sections()[2]  # Goal section
        quota = config.items(quota)[index][1]  # A string variable
        if int(num_drop) >= int(quota) and int(quota) != 0:
            # If the quota exists and has been met
            change_color(driver, index, "Blue")
        elif num_drop == prev_val[index]:
            # If the current qty equals the previous qty
            inactivity = config.sections()[3]  # Inactivity section
            time_limit = config.items(inactivity)[index][1]  # In minutes
            if time_limit == "x":  # There is no time limit
                return  # Exit this iteration
            if (inact[index] >= int(time_limit)) and (red_mark[index] == False):
            # If the time passed without a new drop equals or exceeds the line's time limit
            # and the font is red
                change_color(driver, index, "Red")
                red_mark[index] = True
        else:
            if red_mark[index] == True:  # if the text is red
                change_color(driver, index, "Green")  # Revert back
                red_mark[index] = False
            inact[index] = 0  # Reset counter
            prev_val[index] = num_drop  # Update previous value

    def toggle_break(page, curr_time, line_break):
        """Signify that a line is on break."""
        if curr_time == line_break[-1]:  # If time for a break toggle
            for go in range(21):  # Move the cursor to the top left of the box
                page.send_keys(Keys.ARROW_LEFT)
            page.send_keys(Keys.ARROW_DOWN)
            page.send_keys(Keys.ARROW_LEFT)  # Maneuver to the right side of the first line
            line_break.pop()  # Remove the last element since that time has now passed
            if line_break[0] == True:  # Turn break off
                page.send_keys(Keys.BACKSPACE)  # Remove the '*'
                line_break[0] = False  # Mark this line as not on break
            else:  # Turn break on
                page.send_keys("*")  # Add an '*' to sigify a break
                line_break[0] = True  # Mark this line as on break
        # On break, don't increment inactivity. Not on break, increment inactivity
        return False if line_break[0] == True else True

    # Variables
    locations = []  # Store the locations for many uses later
    previous_values = []  # Store the previous qty's
    for line in config.items(lines):  # Get the corresponding value in the file
        locations.append(line[1])  # Get line name
        previous_values.append(get_qty(remote, line[1]))  # Initial qty's for comparison
    red_markers = [False] * line_num  # Keeps track of which lines are red
    section = config.sections()[4]  # Breaks section
    breaks = []
    for index, line in enumerate(config.items(lines)):  # Get the break times for lines
        breaks.append([])  # Add a list for a line
        for _time_ in (line[1].split(',')):  # Iterating over a list of break periods
            if '-' not in _time_:  # If the Breaks section contains errors
                print("Incorrect format for breaks in Breaks section of .ini file")
                # The program resetting isn't going to fix that, so end it all
                remote.quit()
                driver.quit()
                exit()
            breaks[index].append((_time_.split('-')[0]).strip())  # Append a break start
            breaks[index].append((_time_.split('-')[1]).strip())  # Append a break end
        # The list is reversed so the most recent times can be popped off the end
        # without affecting the placement of the boolean marker
        breaks[index] = breaks[index][::-1]
        breaks[index].insert(0, False)  # Put a False at the beginning
    inactives = [0] * line_num  # Keep track of minutes passed for each message
    exit_condition = False  # Will be False until the natural end is reached

    # The continuous process
    while not exit_condition:  # This goes until someone closes command prompt or the end time is reached
        time.sleep(1)  # This prevents the while loop from executing about a billion times a minute
        current_second = time.strftime("%S", time.localtime())
        if current_second == "00":
            clock = get_time()
            if clock == "4:30":  # Stop updating at the end of the day
                exit_condition = True
                break

            find_by(driver, "name", "B004", 1)
            find_by(driver, "id", "MS000C1", 1)
            find_by(driver, "id", "MS001C1", 1)
            messages = find_by(driver, "id", "MessageEditorText")
            for index in line_num:  # For each line
                update(message, clock, locations[index], breaks[index])  # Where time and qty get changed
                if toggle_break(clock, breaks[index]):  # Check if a break is on
                    inactives[index] += 1  # Increase the minutes passed for the current line

            for index in range(line_num):
                # Go through the boards again to check their inactivity time,
                # because apparently trying to perform the standard update 
                # alongside the inactivity checking causes an error
                check_txt_color(index, locations, previous_values, red_markers, inactives)

            find_by(driver, "name", "Save", 1)
            find_by(driver, "id", "MS000C1", 1)
            find_by(driver, "name", "Main", 1)
        elif current_second == "30":  # Halfway through every minute
            # "Reset" the board window session time
            time.sleep(1)
            # locateOnScreen function needed as using selenium to 
            # click the logout button freezes the program
            auto.click(auto.locateOnScreen("Logout.png"))
            time.sleep(1)
            auto.keyDown("ctrl")  # Refresh the page
            auto.press("r")
            auto.keyUp("ctrl")
            login()

def setup_message(driver, remote, config):
    """Use 'create new msg' to print the initial message."""
    def write_message():
        """Put the correct information in the text boxes."""
        temp = driver.find_element_by_xpath("//* [contains( text(),' of ')]")  # Get # of #
        for f in int(temp.text.split()[-1])-1:  # Delete all previous pages
            find_by(driver, "id", "MS4001C1", 1)
        for j in range(line_num-1):  # Add a page for each line
            find_by(driver, "id", "MS4000C1", 1)
        for index in line_num:
            message = find_by(driver, "id", "MessageEditorText")
            location = lines[index][1]  # Get the corresponding value in the file
            total = get_qty(remote, location)

            message.send_keys(get_time())
            message.send_keys(Keys.RETURN)

            trunc_loc = printing_lines[index][1]  # Printing lines
            message.send_keys(trunc_loc)
            message.send_keys(Keys.RETURN)
            message.send_keys(total)  # Fill in with value from Plex

            section = config.sections()[2]  # Goal section
            quota = config.items(section)[index][1]
            if int(quota) != 0:  # If there's a quota for the day
                message.send_keys("/")
                message.send_keys(quota)

            find_by(driver, "id", "MS9001C1", 1)  # Change alignment

    # Navigate to create new message
    find_by(driver, "id", "MS4001C1", 1)  # Blank the board
    time.sleep(5)
    find_by(driver, "id", "MS4003C1", 1)  # Quick Message
    find_by(driver, "id", "MS1001C1", 1)  # Create new message

    write_message()

    find_by(driver, "id", "MS12000C1", 1)  # Save message
    find_by(driver, "id", "MS1000C1", 1)  # Activate message

def setup_plex(remote):
    """Get plex ready for use."""
    remote.get("https://www.plexonline.com/modules/systemadministration/login/index.aspx")
    find_by(remote, "name", "txtUserID").send_keys("w.Andre.Le")
    find_by(remote, "name", "txtPassword").send_keys("FmSb234_po")  #OokyOoki2  #dArk48_kF
    find_by(remote, "name", "txtCompanyCode").send_keys("wanco")
    find_by(remote, "id", "btnLogin", 1)
    remote.switch_to.window(remote.window_handles[1])
    # Navigate to Production History
    action = ActionChains(remote)
    action.key_down(Keys.CONTROL).send_keys('M').key_up(Keys.CONTROL).perform()
    action = 404
    time.sleep(1)
    action = ActionChains(remote)
    action.send_keys("Production History").send_keys(Keys.RETURN).perform()
    action = 404
    time.sleep(1)
    auto.click(auto.locateOnScreen("PH.png"))

def setup_board(driver):
    """Get the board ready for use."""
    driver.get("http://192.168.13.100:82/")  # Open the IP address
    login()
    try:  # 90% of the html are nested within frames, specifically the second frame
        frames = driver.find_elements_by_tag_name("frame")
        driver.switch_to.frame(frames[1])
        # Going to frame enables access to the rest of the html
    except:  # If the program restarts itself, it doesn't need to do the above again
        pass
    try:  # If left on Quick Message
        find_by(driver, "id", "MS3001C1", 1)
    except:  # If not, the site is either on the main page or elsewhere
        pass
    try:  # If left on Message Edit
        find_by(driver, "id", "MS12002C1", 1)
    except:  # If not, the site is on the main page
        pass

def main(driver, remote, config):
    setup_board(driver)
    setup_plex(remote)

    time.sleep(2)
    setup_message(driver, remote, config)
    time.sleep(5)
    update_board(driver, remote, config)

PATH = "chromedriver.exe"  # Put chromedriver.exe into the same directory
config = ConfigParser()
if config.read('KPIt.ini'):
    print("KPIt.ini file successfully read in")
    lines = config.items(config.sections()[0])
    printing_lines = config.items(config.sections()[1])
    line_num = len(lines)
else:
    print("Couldn't read in KPIt.ini, make sure it's in the same directory")
    exit()

restart = True
while restart:  # The program will restart itself if an error occurs
    try:
        remote = webdriver.Chrome(PATH)  # Make the webdriver for plex first
        # That way, the webdriver for the message board will be the active window
        driver = webdriver.Chrome(PATH)
        main(driver, remote, config)
        restart = False
    except Exception as e:
        print("As error has occurred: ", e.__class__)
        print("Restarting program")
    finally:
        remote.quit()  # It's very important that quit is called on both drivers
        driver.quit()  # This will ensure the error producing webdriver sessions no longer occupy memory
