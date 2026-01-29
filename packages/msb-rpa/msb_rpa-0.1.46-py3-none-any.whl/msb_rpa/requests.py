"""
Module for HTTPS requests and Selenium Wire driver.
"""
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

driver = None


def get_driver_selenium_wire():
    """Hent driver"""
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--disable-search-engine-choice-screen")
        driver = webdriver.Chrome(options=chrome_options)
    return driver
