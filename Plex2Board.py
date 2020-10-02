#IMPORTANT
"""If command prompt raises an error and that error says timeout:
Before you close the program, make sure the message board window (mbw)
is on the main menu. Then try starting the program again.
Most of the timeout errors occur because any action taken
on the mbw start from the main menu. So
the program will try to look for a button only found
on the main menu even if the window is on another page.
With this in mind, even if the program is working as
intended, it'll close itself when 4:30 pm hits.
Closing the program earlier than that will require
the user to navigate the mbw back
to the main menu before closing."""
"""When running the program, let the computer and mouse
alone until the mbw successfully logs in.
After this, the computer can be used for other purposes.
However, don't disrupt the new message board or plex 
windows (pw). Random clicking on the mbw can lead
to the timeout error above. Random clicking on the
pw can lead to the clickinterrupted error.
Last, minimizing or shrinking the new windows 
will likely lead to the 'cannot operate' error.
Basically, if a human can't click it then
the program can't either."""

import pyautogui as auto
import time
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys  # Allows access to non character keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from configparser import ConfigParser

def locate_by_name(web_driver, name):
    """Clicks on something by name."""
    WebDriverWait(web_driver, 10).until(
            EC.presence_of_element_located((By.NAME, name))).click()
    # Returns nothing

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
    reg_time = time.strftime("%H:%M", time.localtime())
    if int(reg_time[:2]) > 12:  # If pm
        reg_time = str(int(reg_time[:2])-12) + reg_time[2:]  # Change to regular time

    return reg_time  # Returns a string

def update_board(driver, remote, config):
    """Will update the time and total on the board."""
    exit_condition = False
    while not exit_condition:  # This goes until someone closes command prompt
        time.sleep(1)  # This prevents the while loop from executing about 
        current_second = time.strftime("%S", time.localtime())
        if current_second == "00":
            if get_time() == "4:30":  # Stop updating at the end of the day
                exit_condition = True
                break
            locate_by_name(driver, "B004")  # Click menu button from main
            locate_by_id(driver, "MS000C1")  # Click 'quick message'
            locate_by_id(driver, "MS001C1")  # Click 'modify msg'
            messages = driver.find_elements(By.NAME, "MessageEditorText")
            for index, message in enumerate(messages):
                for go in range(3):  # Get to the top of the text box
                   message.send_keys(Keys.ARROW_UP)
                message.send_keys(Keys.ARROW_DOWN)
                message.send_keys(Keys.ARROW_LEFT)  # Maneuver to the right side of the first line
                for go in range(5):  # Clear everything on this line
                    message.send_keys(Keys.BACKSPACE)
                message.send_keys(get_time())

                for go in range(3):  # Go one line beyond the last line
                    message.send_keys(Keys.ARROW_DOWN)
                for go in range(6):  # Go to just after the current total
                    message.send_keys(Keys.ARROW_LEFT)
                all_lines = message.text.split()
                if len(all_lines[2]) == 2:  # If the current total has two digits
                    message.send_keys(Keys.BACKSPACE)  # Backspace one more time
                message.send_keys(Keys.BACKSPACE)  # Always backspace at least once
                section = config.sections()[0]  # Workcenter section
                location = config.items(section)[index][1]  # Get the corresponding value in the file
                message.send_keys(get_qty(remote, location))
            locate_by_name(driver, "Save")
            locate_by_id(driver, "MS000C1")  # Click activate msg
            locate_by_name(driver, "Main")

def setup_message(driver, remote, config):
    """Use 'create new msg' to print the initial message."""
    def set_style(page):
        """Set the starting style."""
        align = "AlignP" + page
        color = "ColorP" + page
        locate_by_name(driver, align)
        select_drop(driver, "AlignA000", "Center")
        select_drop(driver, "AlignA001", "Center")
        select_drop(driver, "AlignA002", "Center")
        locate_by_name(driver, "Ok")
        locate_by_name(driver, color)
        select_drop(driver, "ColorA000", "Green")
        select_drop(driver, "ColorA001", "Green")
        select_drop(driver, "ColorA002", "Green")
        locate_by_name(driver, "Ok")

    def write_message():
        """Put the correct information in the text boxes."""
        locate_by_name(driver, "AddPage")
        messages = driver.find_elements(By.NAME, "MessageEditorText")
        for index in range(len(messages)):
            section = config.sections()[0]  # Workcenter section
            location = config.items(section)[index][1]  # Get the corresponding value in the file
            total = get_qty(remote, location)

            messages[index].send_keys(get_time())
            messages[index].send_keys(Keys.RETURN)
            messages[index].send_keys(location)
            messages[index].send_keys(Keys.RETURN)
            messages[index].send_keys(total)  # Fill in with value from Plex

            section = config.sections()[1]  # Goal section
            quota = config.items(section)[index][1]
            if int(quota) != 0:  # If there's a quota for the day
                messages[index].send_keys(Keys.SPACE)
                messages[index].send_keys("/")
                messages[index].send_keys(Keys.SPACE)
                messages[index].send_keys(quota)

    locate_by_name(driver, "B004")
    for do_twice in range(2):
        locate_by_id(driver, "MS000C1")

    write_message()
    set_style("0")
    set_style("1")

    locate_by_name(driver, "Save")
    locate_by_id(driver, "MS000C1")
    locate_by_name(driver, "Main")

def setup_plex(remote):
    """Get plex ready for use."""
    remote.get("https://www.plexonline.com/modules/systemadministration/login/index.aspx?")
    remote.find_element_by_name("txtUserID").send_keys("w.Andre.Le")
    remote.find_element_by_name("txtPassword").send_keys("Uline12UK")
    remote.find_element_by_name("txtCompanyCode").send_keys("wanco")
    locate_by_id(remote, "btnLogin")
    remote.switch_to.window(remote.window_handles[1])
    locate_by_id(remote, "tableMenuNode1")
    locate_by_id(remote, "tableMenuNode4")
    locate_by_id(remote, "tableMenuNode0")
    locate_by_id(remote, "tableMenuNode11")

def setup_board(driver):
    """Get the board ready for use."""
    driver.get("http://192.168.13.100:82/")  # Open the IP address
    auto.write("admin")  # Since the username field is already active and embedded, write admin
    auto.write(["tab"])  # Go to the password field
    auto.write("administrator")
    auto.write(["enter"])
    try:  # 90% of the html are nested within frames, specifically the second frame
        frames = driver.find_elements_by_tag_name("frame")
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it(frames[1]))
        # Going to frame enables access to the rest of the html
    except:  # When the program restarts itself, it doesn't need to do the above again
        pass
    try:  # If a Main button exists, click it to go back to the main menu
        locate_by_name(driver, "Main")
    except:  # If not, the page is already on the main menu and ready to begin
        pass

def main(driver, remote):
    config = ConfigParser()
    config.read('KPIt.ini')
    setup_board(driver)
    setup_plex(remote)

    time.sleep(2)
    setup_message(driver, remote, config)
    time.sleep(5)
    update_board(driver, remote, config)

    finished = False
    while not finished:
        try:
            locate_by_name(driver, "Main")  # Click the Main button after clearing
            finished = True
            break
        except:
            locate_by_name(driver, "B000")  # Try to clear the board

PATH = "C:\Program Files (x86)\chromedriver.exe"
restart = True
while restart:  # The program will restart itself if an error occurs
    try:
        remote = webdriver.Chrome(PATH)  # Find chromedriver.exe and make a driver with Google Chrome
        driver = webdriver.Chrome(PATH)  # Make a second driver
        main(driver, remote)
        restart = False
    except:
        print("Restarting program")
        remote.quit()
        driver.quit()

# Additional Implementations:
# Change the font to red for a line if their total hasn't increased within the inactivity time frame
# Remove the extra 0 from am times
# Make the times include am and pm
# Make the program stop at 4:30 pm