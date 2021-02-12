# For a 3x4 board

import pyautogui as auto
import time
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys  # Allows access to non character keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from configparser import ConfigParser  # Needed to read in from .ini files

def locate_by_name(web_driver, name):
    """Clicks on something by name."""
    WebDriverWait(web_driver, 10).until(
            EC.presence_of_element_located((By.NAME, name))).click()
    # Returns nothing

def find_by_name(web_driver, name):
    """Finds an element by name and returns it."""
    return WebDriverWait(web_driver, 10).until(
            EC.presence_of_element_located((By.NAME, name)))

def locate_by_id(web_driver, id):
    """Clicks on something by id."""
    WebDriverWait(web_driver, 10).until(
            EC.presence_of_element_located((By.ID, id))).click()
    # Returns nothing

def select_drop(web_driver, id, value):
    """Chooses an option by value in a dropdown box by id."""
    select = Select(web_driver.find_element_by_id(id))
    select.select_by_value(value)
    # Returns nothing

def get_qty(web_driver, location):
    """Returns the current total dropped by one line."""
    input_box = WebDriverWait(web_driver, 10).until(
            EC.presence_of_element_located((By.ID, "flttxtWorkcenter")))
    input_box.clear()
    input_box.send_keys(location)
    for i in range(2):
        locate_by_id(web_driver, "SubmitLink")
    try:
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

def change_color(driver, index, colour):
    """Changes the text color for one message."""
    color = "ColorP" + str(index)
    locate_by_name(driver, color)
    select_drop(driver, "ColorA000", colour)
    select_drop(driver, "ColorA001", colour)
    select_drop(driver, "ColorA002", colour)
    locate_by_name(driver, "Ok")

def change_align(driver, index):
    """Changes the text alignment for one message."""
    align = "AlignP" + str(index)
    locate_by_name(driver, align)
    select_drop(driver, "AlignA000", "Center")
    select_drop(driver, "AlignA001", "Center")
    select_drop(driver, "AlignA002", "Center")
    locate_by_name(driver, "Ok")

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
    section = config.sections()[0]  # Workcenter section
    for line in config.items(section):  # Get the corresponding value in the file
        locations.append(line[1])  # Get line name
        previous_values.append(get_qty(remote, line[1]))  # Initial qty's for comparison
    red_markers = [False] * line_num  # Keeps track of which lines are red
    section = config.sections()[4]  # Breaks section
    breaks = []
    for index, line in enumerate(config.items(section)):  # Get the break times for lines
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

            locate_by_name(driver, "B004")  # Click menu button from main
            locate_by_id(driver, "MS000C1")  # Click 'quick message'
            locate_by_id(driver, "MS001C1")  # Click 'modify msg'
            messages = driver.find_elements(By.NAME, "MessageEditorText")
            for index, message in enumerate(messages):  # For each line
                if toggle_break(message, clock, breaks[index]):  # Check if a break is on
                    inactives[index] += 1  # Increase the minutes passed for the current line
                update(message, clock, locations[index], breaks[index])  # Where time and qty get changed

            for index in range(line_num):
                # Go through the boards again to check their inactivity time,
                # because apparently trying to perform the standard update 
                # alongside the inactivity checking causes an error
                check_txt_color(index, locations, previous_values, red_markers, inactives)

            time.sleep(1)
            locate_by_name(driver, "Save")
            locate_by_id(driver, "MS000C1")  # Click activate msg
            locate_by_name(driver, "Main")
        elif current_second == "30":  # Halfway through every minute
            # "Reset" the board window session time
            time.sleep(1)
            # locateOnScreen function needed as using selenium to 
            # click the logout button freezes the program
            auto.click(auto.locateOnScreen("Logout.png"))
            time.sleep(1)
            auto.click(auto.locateOnScreen("Login.png"))
            login()
            locate_by_name(driver, "Main")

def setup_message(driver, remote, config):
    """Use 'create new msg' to print the initial message."""
    def write_message():
        """Put the correct information in the text boxes."""
        for j in range(line_num-1):  # Add a page for each line
            locate_by_name(driver, "AddPage")
        messages = driver.find_elements(By.NAME, "MessageEditorText")
        for index, message in enumerate(messages):
            section = config.sections()[0]  # Workcenter section
            location = config.items(section)[index][1]  # Get the corresponding value in the file
            total = get_qty(remote, location)

            message.send_keys(get_time())
            message.send_keys(Keys.RETURN)

            section = config.sections()[1]  # PrintingName section
            trunc_loc = config.items(section)[index][1]
            message.send_keys(trunc_loc)
            message.send_keys(Keys.RETURN)
            message.send_keys(total)  # Fill in with value from Plex

            section = config.sections()[2]  # Goal section
            quota = config.items(section)[index][1]
            if int(quota) != 0:  # If there's a quota for the day
                message.send_keys("/")
                message.send_keys(quota)

    # Navigate to create new message
    locate_by_name(driver, "B004")
    for do_twice in range(2):
        locate_by_id(driver, "MS000C1")

    write_message()
    for panel_num in range(line_num):
        change_color(driver, panel_num, "Green")
        change_align(driver, panel_num)

    locate_by_name(driver, "Save")
    locate_by_id(driver, "MS000C1")
    locate_by_name(driver, "Main")

def setup_plex(remote):
    """Get plex ready for use."""
    remote.get("https://www.plexonline.com/modules/systemadministration/login/index.aspx?")
    remote.find_element_by_name("txtUserID").send_keys("w.Andre.Le")
    remote.find_element_by_name("txtPassword").send_keys("OokyOoki2")
    remote.find_element_by_name("txtCompanyCode").send_keys("wanco")
    locate_by_id(remote, "btnLogin")
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
    action = ActionChains(remote)
    action.send_keys(Keys.DOWN).send_keys(Keys.RETURN).perform()
    time.sleep(1)

def setup_board(driver):
    """Get the board ready for use."""
    driver.get("http://192.168.13.100:82/")  # Open the IP address
    login()
    try:  # 90% of the html are nested within frames, specifically the second frame
        frames = driver.find_elements_by_tag_name("frame")
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it(frames[1]))
        # Going to frame enables access to the rest of the html
    except:  # If the program restarts itself, it doesn't need to do the above again
        pass
    try:  # If a Main button exists, click it to go back to the main menu
        locate_by_name(driver, "Main")
    except:  # If not, the page is already on the main menu and ready to begin
        pass

def main(driver, remote, config):
    setup_board(driver)
    setup_plex(remote)

    time.sleep(2)
    setup_message(driver, remote, config)
    time.sleep(5)
    update_board(driver, remote, config)
    # The below executes at the end
    finished = False
    while not finished:
        try:
            locate_by_name(driver, "Main")  # Click the Main button after clearing
            finished = True
            break
        except:
            locate_by_name(driver, "B000")  # Try to clear the board

PATH = "chromedriver.exe"  # Put chromedriver.exe into the same directory
config = ConfigParser()
if config.read('KPIt.ini'):
    print("KPIt.ini file successfully read in")
    lines = config.sections()[0]
    line_num = len(config.items(lines))
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
