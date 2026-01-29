"""
Login Module

This module contains functions for logging into various systems and applications,
including Fasit, KMD BogV, and Opus.

Dependencies:
- Selenium
- Pywinauto
- Pyautogui
"""
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pywinauto import Application, findwindows
import pyautogui
from msb_rpa.web import get_driver
from msb_rpa.web import get_driver_chrome_incognito
from msb_rpa.web import get_driver_autodownload
from msb_rpa.requests import get_driver_selenium_wire
from msb_rpa.web import close_website_panes
from msb_rpa.generelt import generate_password
from msb_rpa.generelt import basic_email

# Constants
WINDOWS_USERNAME = os.getenv('USERNAME')
DOWNLOAD_DIRECTORY = f"C:\\Users\\{WINDOWS_USERNAME}\\Downloads"


def fasit_login(username: str, password: str, timers=None, drivertype: str = 'chrome', folder: str = r"C:\temp"):
    """
    Logger ind i Fasit (https://login.fasit.dk/aarhus/aak) ved at indtaste brugernavn og password

    Args:
        username (str): Fasit username.
        password (str): Fasit password.
        timers (str): Pass in timers extracted from OpenOrchestrator. If not default value is: timers = {"sleep_time": 2, "long_sleep_time": 5, "wait_time": 15, "long_wait_time": 30}
        drivertype (str): 'chrome', 'chrome_incognito', 'chrome_wire' or 'chrome_download' to download content into specified folder.
        If 'chrome_download' is used as drivertype, pass in a raw string to a folderpath to escape backslashes or use default r"C:\temp".
        If 'chrome_wire' is selected a bearer token is returned, which can be stored in a variable and used for API calls.
    """
    if timers is None:
        timers = {"sleep_time": 2, "long_sleep_time": 5, "wait_time": 15, "long_wait_time": 30}
    url = "https://login.fasit.dk/aarhus/aak"
    if drivertype == 'chrome_download':
        driver = get_driver_autodownload(folder)
    elif drivertype == 'chrome_incognito':
        driver = get_driver_chrome_incognito()
    elif drivertype == 'chrome_wire':
        driver = get_driver_selenium_wire()
    else:
        driver = get_driver()
    driver.get(url)
    driver.maximize_window()
    shortwait = WebDriverWait(driver, timers["long_sleep_time"])
    wait = WebDriverWait(driver, timers["wait_time"])
    longwait = WebDriverWait(driver, timers["long_wait_time"])

    # BRUGERNAVN INDTASTES.
    element = longwait.until(EC.visibility_of_element_located((By.NAME, "loginfmt")))
    element.send_keys(username)
    time.sleep(timers["sleep_time"])

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()
    time.sleep(timers["sleep_time"])

    # PASSWORD INDTASTES.
    element = wait.until(EC.visibility_of_element_located((By.NAME, "passwd")))
    element.send_keys(password)

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()

    search = longwait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="layout__app-header"]//div[@class="MuiBox-root css-0"]')))
    logged_in_tekst = search.text
    print(logged_in_tekst)

    if drivertype == 'chrome_wire':
        time.sleep(8)
        # Iterate through captured requests to find the one with the Bearer token
        for request in driver.requests:
            if request.response and 'Authorization' in request.headers:
                parts = request.headers['Authorization'].split()
                # Check if the header has the correct format and starts with 'Bearer'
                if len(parts) == 2 and parts[0] == 'Bearer':
                    bearer_token = parts[1]  # Extract Bearer token
                    close_website_panes()
                    return bearer_token

        # If the loop completes without finding a bearer token, raise an exception
        raise Exception("Bearer token not found in captured requests.")

    try:
        infotekst = shortwait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Luk meddelelser"]')))
        infotekst.click()
    except Exception:
        print("infotekst poppede ikke op")


def bogv_login(username, password):
    """
    Logger ind i KMD BogV windows applikationen.

    Parameters:
        username (str): The username for login.
        password (str): The password for login.

    Requirements:
        - KMD BogV must be installed at the default path.
        - Requires `pywinauto` and `pyautogui` libraries.

    """
    program_path = r'C:\Program Files (x86)\KMD\BogV\BogV.exe'
    app = Application(backend='uia').start(program_path, timeout=10)
    app = Application(backend="uia").connect(title="Tilslutning til KMD", class_name="ThunderRT6FormDC")

    kmd_bogv = app.window(title="Tilslutning til KMD", class_name="ThunderRT6FormDC")
    kmd_bogv.set_focus()

    brugernavn = kmd_bogv.child_window(auto_id='7')
    brugernavn.click_input()
    pyautogui.typewrite(username, interval=0.1)

    passwordfelt = kmd_bogv.child_window(auto_id='6')
    passwordfelt.click_input()
    pyautogui.typewrite(password, interval=0.1)

    loginknap = kmd_bogv.child_window(title="Logon", auto_id="4", control_type="Button")
    loginknap.click_input()


# Opus Login
def opus_login(username: str, password: str, credential_name: str):
    """
    Logger ind i desktop udgaven af OPUS

    Parameters:
        username (str): The username for login.
        password (str): The password for login.
        credential_name (str): Used in case there is a need to update the password.

    Returns:
        None: If the login was successful.
        New Password (str): If there was a need for a password change.
    """
    driver = get_driver()

    wait = WebDriverWait(driver, 10)
    url = "https://portal.kmd.dk/irj/portal"

    new_pw = None

    driver.get(url)
    driver.maximize_window()

    element = wait.until(EC.visibility_of_element_located((By.ID, "logonuidfield")))
    element.send_keys(username)

    element = wait.until(EC.visibility_of_element_located((By.ID, "logonpassfield")))
    element.send_keys(password)

    element = wait.until(EC.element_to_be_clickable((By.ID, "buttonLogon")))
    element.click()

    try:
        wait.until(EC.element_to_be_clickable((By.ID, "topLevelNavigationTR")))
    except TimeoutException:
        new_pw = generate_password()

        old_pw = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="inputUsername"]')))
        old_pw.send_keys(password)

        new_pw_first = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="j_sap_password"]')))
        new_pw_first.send_keys(new_pw)

        new_pw_second = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="j_sap_again"]')))
        new_pw_second.send_keys(new_pw)

        skift_button = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="changeButton"]')))
        skift_button.click()

        basic_email(["lfrmi@aarhus.dk", "aeta@aarhus.dk", "du@msb.aarhus.dk"], f"Password ændret på {credential_name}",
            f"""<html>
            <body>
            <p>Password på {credential_name} ændret fra {password} til {new_pw}</p>
            <p></p>
            <p>Husk at opdatere {credential_name} på OpenOrchestrator på Udvikling + Onenote</p>
            </body>
            </html>""")

        xpath_expression = '//div[@displayname="Mine Genveje" and starts-with(@id, "tabIndex")]'
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_expression)))
        element.click()

        time.sleep(5)
        files = os.listdir(DOWNLOAD_DIRECTORY)
        for file in files:
            if file.endswith("tx.sap"):
                os.system(f"start {DOWNLOAD_DIRECTORY}\\{file}")
                break

        time.sleep(10)
        _opus_aabn()
        close_website_panes()

        return new_pw

    xpath_expression = '//div[@displayname="Mine Genveje" and starts-with(@id, "tabIndex")]'
    element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_expression)))
    element.click()

    time.sleep(5)
    files = os.listdir(DOWNLOAD_DIRECTORY)
    for file in files:
        if file.endswith("tx.sap"):
            os.system(f"start {DOWNLOAD_DIRECTORY}\\{file}")
            break

    time.sleep(10)
    _opus_aabn()
    close_website_panes()

    return new_pw


def _opus_aabn():
    """
    Handles opening and interacting with the SAP window after Opus login.
    """
    sap_window_title = "Information"
    try:
        sap_window_handle = findwindows.find_window(title=sap_window_title)
        sap_window_gw = Application(backend="uia").connect(handle=sap_window_handle)
        sap_app_window = sap_window_gw.window(title=sap_window_title, handle=sap_window_handle)
        sap_app_window.set_focus()

        app_toolbar = sap_app_window.child_window(title="AppToolbar")
        if app_toolbar:
            fortset_button = app_toolbar.child_window(title="Fortsæt")
            fortset_button.wait("enabled", timeout=10)
            if fortset_button:
                fortset_button.click_input()
    except Exception:
        print("vindue ikke fundet")


def opus_online_login(username: str, password: str, credential_name: str):
    """
    Logger ind i online udgaven af OPUS

    Parameters:
        username (str): The username for login.
        password (str): The password for login.
        credential_name (str): Used in case there is a need to update the password.

    Returns:
        None: If the login was successful.
        New Password (str): If there was a need for a password change.
    """
    driver = get_driver()
    wait = WebDriverWait(driver, 10)
    url = "https://portal.kmd.dk/irj/portal"

    new_pw = None

    driver.get(url)
    driver.maximize_window()

    element = wait.until(EC.visibility_of_element_located((By.ID, "logonuidfield")))
    element.send_keys(username)

    element = wait.until(EC.visibility_of_element_located((By.ID, "logonpassfield")))
    element.send_keys(password)

    element = wait.until(EC.element_to_be_clickable((By.ID, "buttonLogon")))
    element.click()

    try:
        wait.until(EC.element_to_be_clickable((By.ID, "topLevelNavigationTR")))
    except TimeoutException:
        new_pw = generate_password()

        old_pw = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="inputUsername"]')))
        old_pw.send_keys(password)

        new_pw_first = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="j_sap_password"]')))
        new_pw_first.send_keys(new_pw)

        new_pw_second = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="j_sap_again"]')))
        new_pw_second.send_keys(new_pw)

        skift_button = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@id="changeButton"]')))
        skift_button.click()

        basic_email(["lfrmi@aarhus.dk", "aeta@aarhus.dk", "du@msb.aarhus.dk"], f"Password ændret på {credential_name}",
            f"""<html>
            <body>
            <p>Password på {credential_name} ændret fra {password} til {new_pw}</p>
            <p></p>
            <p>Husk at opdatere {credential_name} på OpenOrchestrator på Udvikling + Onenote</p>
            </body>
            </html>""")

        return new_pw

    return new_pw


def modulus_login(username: str, password: str, drivertype: str = 'chrome', folder: str = r"C:\temp"):
    """
    Logger ind i Modulus Social - Aarhus Kommune B2C

    Parameters:
        username (str): The username for login.
        password (str): The password for login.
        drivertype (str): 'chrome', 'chrome_download', 'chrome_incognito' or 'chrome_wire'.
        If 'chrome_download' is used as drivertype, pass in a raw string to a folderpath to escape backslashes or use default r"C:\temp".
        If 'chrome_wire' is selected a bearer token is returned, which can be stored in a variable and used for API calls.
    """
    if drivertype == 'chrome_incognito':
        driver = get_driver_chrome_incognito()
    elif drivertype == 'chrome_download':
        driver = get_driver_autodownload(folder)
    elif drivertype == 'chrome_wire':
        driver = get_driver_selenium_wire()
    else:
        driver = get_driver()

    url = "https://aarhus.modulussocial.dk"
    driver.get(url)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # Autentificeringsmetode vælges.
    element_metode = wait.until(EC.element_to_be_clickable((By.XPATH, '//option[contains(text(), "Aarhus Kommune B2C")]')))
    element_metode.click()

    # Der klikkes på knappen "OK.".
    element_ok = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@value="OK"]')))
    element_ok.click()

    # Brugernavn indtkastes.
    element_bruger = wait.until(EC.visibility_of_element_located((By.NAME, "loginfmt")))
    element_bruger.send_keys(username)
    time.sleep(1)

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()
    time.sleep(1)

    # Password indtastes.
    element_kode = wait.until(EC.visibility_of_element_located((By.NAME, "passwd")))
    element_kode.send_keys(password)

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()

    if drivertype == 'chrome_wire':
        time.sleep(5)
        # Iterate through captured requests to find the one with the Bearer token
        for request in driver.requests:
            cookie_header = request.headers.get('Cookie', '')
            if request.response and '.AspNetCore.saml2.cookies=' in cookie_header:
                bearer_token = request.headers['Cookie']  # Extract Bearer token
                close_website_panes()
                return bearer_token

        # If the loop completes without finding a bearer token, raise an exception
        raise Exception("Bearer token not found in captured requests.")


def bam_login(username: str, password: str):
    """Logger ind i BAM"""
    driver = get_driver_chrome_incognito()

    # Brugernavn og password indtastes samtidig med url
    url = f"http://{username}:{password}@srvappbam01/Brugeradm/"

    driver.get(url)
    driver.maximize_window()


def mira_login(username: str, password: str):
    """
    Logger ind i Mira

    Parameters:
        username (str): The username for login.
        password (str): The password for login.
    """
    driver = get_driver()

    url = "https://miraapp.dk/"
    driver.get(url)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)
    longwait = WebDriverWait(driver, 20)

    time.sleep(10)

    pyautogui.press('tab')  # Press Tab once
    pyautogui.press('tab')  # Press Tab again
    pyautogui.press('enter')  # Press Enter

    # BRUGERNAVN INDTASTES.
    element = longwait.until(EC.visibility_of_element_located((By.NAME, "loginfmt")))
    element.send_keys(username)
    time.sleep(2)

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()
    time.sleep(2)

    # PASSWORD INDTASTES.
    element = wait.until(EC.visibility_of_element_located((By.NAME, "passwd")))
    element.send_keys(password)

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()

    indstillinger = longwait.until(EC.element_to_be_clickable((By.XPATH, '//a[text()="Indstillinger"]')))
    print(indstillinger.text)


def ky_login(username: str, password: str, timers=None):
    """
    Logger ind i KY (https://fs0751.fs.kommunernesydelsessystem.dk/ky-fagsystem/)

    Args:
        username (str): Fasit username.
        password (str): Fasit password.
        timers (str): Pass in timers extracted from OpenOrchestrator. If not default value is: timers = {"sleep_time": 2, "long_sleep_time": 5, "wait_time": 15, "long_wait_time": 30}
    """

    url = "https://fs0751.fs.kommunernesydelsessystem.dk/ky-fagsystem/"
    timers = {"sleep_time": 2, "long_sleep_time": 5, "wait_time": 15, "long_wait_time": 30}
    driver = get_driver()
    driver.get(url)
    driver.maximize_window()
    wait = WebDriverWait(driver, timers["wait_time"])
    longwait = WebDriverWait(driver, timers["long_wait_time"])

    # Autentificeringsmetode vælges.
    element_metode = wait.until(EC.element_to_be_clickable((By.XPATH, '//option[contains(text(), "Aarhus Kommune B2C")]')))
    element_metode.click()

    # Der klikkes på knappen "OK.".
    element_ok = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@value="OK"]')))
    element_ok.click()

    # BRUGERNAVN INDTASTES.
    element = longwait.until(EC.visibility_of_element_located((By.NAME, "loginfmt")))
    element.send_keys(username)
    time.sleep(timers["sleep_time"])

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()
    time.sleep(timers["sleep_time"])

    # PASSWORD INDTASTES.
    element = wait.until(EC.visibility_of_element_located((By.NAME, "passwd")))
    element.send_keys(password)

    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    element.click()

    search = longwait.until(EC.presence_of_element_located((By.XPATH, '//span[text()="KOMMUNERNES YDELSESSYSTEM"]')))
    logged_in_tekst = search.text
    print(logged_in_tekst)
