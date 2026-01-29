"""
Module for managing browser tabs and WebDriver operations using Selenium.
"""
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoAlertPresentException

driver = None


def get_driver():
    """Global webdriver"""
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--disable-search-engine-choice-screen")
        driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_driver_autodownload(folder: str = r"C:\temp"):
    """
    Global webdriver, where files automatically is downloaded to specified folder

    Args:
    folder (str): The folder to save the file in. Defaults to r"C:\temp".

    NB! Remember to pass folder name as a raw string to handle backslashes properly!
    """
    global driver
    if driver is None:
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', {
        "download.default_directory": folder,  # Change default directory for downloads
        "download.prompt_for_download": False,  # To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True  # It will not show PDF directly in chrome
        })
        options.add_argument("--disable-search-engine-choice-screen")
        driver = webdriver.Chrome(options=options)
    return driver


def get_driver_chrome_incognito():
    """Global webdriver"""
    global driver
    if driver is None:
        # Configure Chrome options for incognito mode
        chrome_options = Options()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-search-engine-choice-screen")
        chrome_options.add_argument("--start-maximized")  # You can adjust this option as needed

        # Create a new Chrome WebDriver instance with the configured options
        driver = webdriver.Chrome(options=chrome_options)

    return driver


def pick_website_pane(target: str, exact_title: bool = False) -> bool:
    """
    Switches to the browser tab that matches the target URL or title of the pane.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        target (str): The target URL/title to find in open browser tabs.
        exact_title (bool): If True, look for an exact title match. Defaults to False.

    Returns:
        bool: True if a tab with the target URL/title is found and switched to, False otherwise.
    """
    global driver
    window_handles = driver.window_handles

    for handle in window_handles:
        driver.switch_to.window(handle)
        if isinstance(target, str):
            if exact_title:
                if target.lower() == driver.title.lower():
                    return True  # Successfully switched to the new window
            else:
                if target.lower() in driver.title.lower():
                    return True  # Successfully switched to the new window
        else:
            if target in driver.current_url:
                return True  # Successfully switched to the new window

    return False  # No window with the target URL or title found


def close_website_panes(target=None):
    """
    Closes browser windows based on the provided target, or all windows if no target is specified.
    Searches for the target in both window titles and URLs.

    Args:
        driver (webdriver): The Selenium WebDriver instance.
        target (str, optional): The target to match against window title or URL.
                                If None, all windows will be closed.
    """
    global driver  # Declare that we're using the global driver variable

    # Check if the driver is initialized and has active windows
    if not driver or not hasattr(driver, 'window_handles') or not driver.window_handles:
        print("No active browser session or windows to close.")
        return

    handles_to_close = []

    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
            print("Dismissed an alert before proceeding.")
        except NoAlertPresentException:
            pass
        if target is None or (target and (re.search(target, driver.title) or re.search(target, driver.current_url))):
            print(f"Marking for closure: Title '{driver.title}', URL '{driver.current_url}'")
            handles_to_close.append(handle)

    for handle in handles_to_close:
        driver.switch_to.window(handle)
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
            print("Dismissed an alert before proceeding.")
        except NoAlertPresentException:
            pass
        driver.close()

        # Check if any windows remain
        try:
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
            else:
                print("All windows closed.")
                driver = None
        except WebDriverException:
            print("Session is already invalid after closing all windows.")
            driver.quit()
            driver = None
