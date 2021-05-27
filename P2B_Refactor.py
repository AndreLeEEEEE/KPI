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
    """
    web_driver - selenium webdriver, any driver
    attribute - string, HTML element
    value - string, HTML element value
    click - integer, signify if element has to be clicked, default is no
    """
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
    """
    web_driver - selenium webdriver, the plex driver
    location - string, full location name for search criteria
    """
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
    """
    driver - selenium webdriver, message board driver
    remote - selenium webdriver, plex driver
    config - config file, holds KPI.ini
    """
    # Inner functions
    def update(index, message, clock, location, break_time, p_values):
        """Where all the writing happens for one panel."""
        """
        index - integer, current page index
        message - selenium element, message box
        clock - string, current time
        location - list of str, name of line to use
        break-time - list of bool and str, break status and times for line
        p_values - list of str, the line's qty before the current one
        """
        message.send_keys(clock)
        if toggle_break(index, message, clock, break_time) == False:  # Check if a break is on or off
                inactives[index] += 1  # Increase the minutes passed for the current line
        message.send_keys(Keys.RETURN)  # Onto next text line

        message.send_keys(printing_lines[index][1])  # The shortened line name
        message.send_keys(Keys.RETURN)  # Onto next text line

        temp_qty = get_qty(remote, location[1])
        message.send_keys(temp_qty)
        section = config.sections()[2]  # Goal section
        quota = config.items(section)[index][1]
        if int(quota) != 0:
            message.send_keys('/' + quota)

        toggle_inactive(index, message, p_values, temp_qty, quota)
        find_by(driver, "name", "Submit", 1)  # Submit changes, alignment already sticks

    def toggle_inactive(index, page, prev_qty, cur_qty, quo):
        """Change the text color of a line when necessary."""
        """
        index - integer, current page index
        page - selenium element, message box
        prev_qty - list of str, the line's qty before the current one
        cur_qty - string, the line's current qty
        quo - string, the line's quota
        """
        inactivity = config.sections()[3]  # Inactivity section
        time_limit = config.items(inactivity)[index][1]  # In minutes
        if (time_limit == "x") or (int(cur_qty) >= int(quo)):
            # If there's no time limit or quota was achieved
            return  # Exit this function
        else:
            if (cur_qty == prev_qty[index]) and (inactives[index] >= int(time_limit)):
                page.send_keys("?")
            else:
                inactives[index] = 0  # Reset counter
                prev_qty[index] = cur_qty  # Update previous value

    def toggle_break(index, page, curr_time, line_break):
        """Signify that a line is on break."""
        """
        index - integer, current page index
        page - selenium element, message box
        curr_time - string, current time
        line_break - list of bool and str, break status and times for line
        """
        if line_break:  # If there's something in the list
            for count, Time in enumerate(line_break[::-1]):
            # The purpose of this loop is to determine how many break times
            # have to be popped prematuraly in the case of a restart. When
            # the latter occurs, all break times are present in line_break.
            # This is a problem if the restart happened after some times 
            # were popped since curr_time is compared to the last element.
                if curr_time <= Time:
                    break
            for go in range(count):
                line_break.pop()

            if curr_time == line_break[-1]:  # If time for a break toggle
                line_break.pop()  # Remove the last element since that time has now passed
                if b_status[index] == True:  # Turn break off
                    b_status[index] = False  # Mark this line as not on break
                else:  # Turn break on
                    b_status[index] = True  # Mark this line as on break
            if b_status[index] == True:
                page.send_keys("*")  # Add an '*' to signify a break
            # On break, don't increment inactivity. Not on break, increment inactivity

        return True if b_status[index] == True else False

    # Variables
    previous_values = []  # Store the previous qty's
    for line in lines:  # Get the corresponding value in the file
        previous_values.append(get_qty(remote, line[1]))  # Initial qty's for comparison
    section = config.sections()[4]  # Breaks section
    breaks = []
    temp_b = config.items(config.sections()[4])  # Get the breaks
    for index, line in enumerate(temp_b):  # Get the break times for lines
        breaks.append([])  # Add a list for a line
        for _time_ in (line[1].split(',')):  # Iterating over a list of break periods
            if ('-' not in _time_):
                # If the Breaks section contains errors
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
        if len(breaks[index]) % 2 != 0:  # If there's an odd number of times
            print("Odd number of times in Breaks section of .ini file")
            # The program resetting isn't going to fix that, so end it all
            remote.quit()
            driver.quit()
            exit()
    exit_condition = False  # Will be False until the natural end is reached

    # The continuous process
    while not exit_condition:  # This goes until someone closes command prompt or the end time is reached
        time.sleep(1)  # This prevents the while loop from executing about a billion times a minute
        current_second = time.strftime("%S", time.localtime())
        if current_second == "00":
            clock = get_time()
            if clock == "4:30":  # Stop updating at the end of the day
                exit_condition = True
                find_by(driver, "id", "MS4001C1", 1)  # Blank the board when done
                continue

            time.sleep(3)
            find_by(driver, "id", "MS4003C1", 1)  # Quick Message
            time.sleep(3)
            driver.find_element_by_xpath("//*[@id='MS1001C1']").click()
            #find_by(driver, "id", "MS1001C1", 1)  # 'Create new' message
            for index in range(line_num):  # For each line
                message = find_by(driver, "id", "MessageEditorText")
                # Passing an integer, selenium element, string, list, list, list
                # previous_values is passed as list since
                # changes made to it need to stick
                update(index, message, clock, lines[index], breaks[index], previous_values)
                if line_num - index != 1:
                    find_by(driver, "id", "MS3001C1", 1)  # Go to next page

            find_by(driver, "id", "MS12000C1", 1)  # Save button
            find_by(driver, "id", "MS1000C1", 1)  # Activate message button
        elif current_second == "30":  # Halfway through every minute
            # "Reset" the board window session time
            # locateOnScreen function needed as using selenium to 
            # click the logout button freezes the program
            auto.click(auto.locateOnScreen("Logout.png"))
            time.sleep(1)
            auto.keyDown("ctrl")  # Refresh the page
            auto.press("r")
            auto.keyUp("ctrl")
            time.sleep(2)
            login()

def setup_message(driver, remote, config):
    """Use 'create new msg' to print the initial message."""
    """
    driver - selenium webdriver, message board driver
    remote - selenium webdriver, plex driver
    config - config file, holds KPI.ini
    """
    def write_message(clock):
        """Put the correct information in the text boxes."""
        """
        clock - string, the current time
        """
        temp = driver.find_element_by_xpath("//* [contains( text(),' of ')]")  # Get # of #
        for f in range(int(temp.text.split()[-1])):  # Delete all previous pages
            find_by(driver, "id", "MS4001C1", 1)  # The delete button
        for index in range(line_num):
            message = find_by(driver, "id", "MessageEditorText")
            location = lines[index][1]  # Get the corresponding value in the file
            total = get_qty(remote, location)

            message.send_keys(clock)
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
            find_by(driver, "name", "Submit", 1)
            # Add a new page, the interface automatically goes to it
            # Unless this is the last page, then don't add new page
            if line_num - index != 1:
                find_by(driver, "id", "MS4000C1", 1)

    # Navigate to create new message
    find_by(driver, "id", "MS4001C1", 1)  # Blank the board
    time.sleep(5)
    find_by(driver, "id", "MS4003C1", 1)  # Quick Message
    time.sleep(3)
    find_by(driver, "id", "MS1001C1", 1)  # Create new message
    # The current time has to be calculated and passed now since it
    # can update between iterations in the function
    write_message(get_time())

    find_by(driver, "id", "MS12000C1", 1)  # Save message
    find_by(driver, "id", "MS1000C1", 1)  # Activate message

def setup_plex(remote):
    """Get plex ready for use."""
    """
    remote - selenium webdriver, plex driver
    """
    remote.get("https://www.plexonline.com/modules/systemadministration/login/index.aspx")
    find_by(remote, "name", "txtUserID").send_keys("w.Andre.Le")
    find_by(remote, "name", "txtPassword").send_keys("FmSb234_po")
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
    """
    driver - selenium webdriver, message board driver
    """
    driver.get("http://192.168.13.100:82/")  # Open the IP address
    login()
    try:  # If left on Quick Message
        find_by(driver, "id", "MS3001C1", 1)
    except:  # If not, the site is either on the main page or elsewhere
        pass
    try:  # If left on Message Edit
        find_by(driver, "id", "MS12002C1", 1)
    except:  # If not, the site is on the main page
        pass

def main(driver, remote, config):
    """Start everything"""
    """
    driver - selenium webdriver, message board driver
    remote - selenium webdriver, plex driver
    config - config file, holds KPI.ini
    """
    setup_board(driver)
    setup_plex(remote)
    auto.click(auto.locateOnScreen("BringForward.png"))

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
    # These variables below are global so they're maintained in case of a restart
    b_status = [False] * line_num  # Break status for every line
    inactives = [0] * line_num  # Keep track of minutes passed for each message
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
        driver.quit()  # This will ensure the webdriver sessions no longer occupy memory