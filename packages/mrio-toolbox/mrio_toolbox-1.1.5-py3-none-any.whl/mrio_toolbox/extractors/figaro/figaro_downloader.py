"""
Download Figaro 25ed from the CIRCABC website.

@author: wirth
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, WebDriverException
import time
import os
import logging 

log = logging.getLogger(__name__)


def wait_for_download(file_path, timeout=60):
    """
    Wait until the given file has been fully downloaded.
    
    Parameters
    ----------
    file_path : str
        The path to the file that is being downloaded.
    timeout : int
        Maximum time to wait for the download to complete, in seconds.
    """
    folder = os.path.dirname(file_path)
    end_time = time.time() + timeout

    while time.time() < end_time:
        # Firefox: file exists, size stops changing
        if os.path.exists(file_path):
            size_old = os.path.getsize(file_path)
            time.sleep(1)
            size_new = os.path.getsize(file_path)
            if size_new == size_old:
                time.sleep(1)  # wait a bit more to ensure download is completed
                return True

        # Chrome: check for any .crdownload temp file
        if not any(name.endswith(".crdownload") for name in os.listdir(folder)):
            if os.path.exists(file_path):
                time.sleep(1)  # wait a bit more to ensure download is completed
                return True
            
        time.sleep(0.5)
    raise TimeoutError(f"Download not completed within {timeout} seconds: {file_path}")

def get_driver(destination, headless=True, prefer="chrome"):
    """
    Try to get a Selenium driver. Falls back to Chrome if Firefox is not available.
    
    Parameters
    ----------
    destination : str
        Download folder for browser.
    headless : bool
        Run browser in headless mode.
    prefer : str
        Preferred browser: "firefox" or "chrome".
    """

    def make_firefox():
        options = FirefoxOptions()
        if headless: options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", destination)
        return webdriver.Firefox(options=options)

    def make_chrome():
        options = ChromeOptions()
        if headless: options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        prefs = {"download.default_directory": destination,
                 "download.prompt_for_download": False,
                 "download.directory_upgrade": True,
                 "safebrowsing.enabled": True,
                 "profile.default_content_setting_values.automatic_downloads": 1}
        options.add_experimental_option("prefs", prefs)
        return webdriver.Chrome(options=options)

    tried = []
    for choice in ([prefer, "chrome", "firefox"] if prefer == "firefox" else [prefer, "firefox", "chrome"]):
        try:
            if choice == "firefox":
                log.info("Trying Firefox driver...")
                return make_firefox()
            elif choice == "chrome":
                log.info("Trying Chrome driver...")
                return make_chrome()
        except WebDriverException as e:
            log.warning(f"{choice.capitalize()} driver failed: {e}")
            tried.append(choice)
    raise RuntimeError(f"Could not start any browser driver (tried {tried}). Please install Firefox or Chrome.")


def safe_click(driver, by, value, description="element"):
    """
    Safely clicks an element on the page, handling exceptions and logging errors.
    
    Parameters:
    -----------
    driver: WebDriver
        The Selenium WebDriver instance.
    by: By
        The method to locate the element (e.g., By.XPATH, By.CSS_SELECTOR).
    value: str
        The value to locate the element.
    description: str
        A description of the element for logging purposes.
        
    Notes:
    ------
    If you want to debug the click, you can set the headless mode to False in the download_figaro function.
    This will open the browser window and allow you to see what is happening. 
    In the browser window, you can right-click on the element and select "Inspect" to see the HTML structure.
    """
    try:
        elem = driver.find_element(by, value)
        driver.execute_script("arguments[0].click();", elem)  # Click with JavaScript to avoid issues with overlays or pop-ups
        log.info(f"Clicked {description}")
    except NoSuchElementException:
        log.error(f"{description} not found: {value}")
        raise RuntimeError(f"{description} not found: {value}. The download was aborted. Likely the page structure of the CIRCABC website has changed. "
                           "If you are a developer, try to debug without headless mode. If you are a user, you may want to download the figaro tables manually.")
    except ElementClickInterceptedException:
        log.error(f"{description} was obstructed: {value}")
        raise RuntimeError(f"{description} was obstructed: {value}. The download was aborted. Likely the page structure of the CIRCABC website has changed."
                           "If you are a developer, try to debug without headless mode. If you are a user, you may want to download the figaro tables manually.")
    except Exception as e:
        log.error(f"Error clicking {description}: {e}.")
        raise RuntimeError("The download was aborted. Likely the page structure of the CIRCABC website has changed."
                           "If you are a developer, try to debug without headless mode. If you are a user, you may want to download the figaro tables manually.")



def download_figaro(year, destination, format = 'industry by industry', sut = False, headless = True): 
    """
    Downloads the specified format of the EU input-output matrix from Figaro.
    
    Parameters:
    -----------
    destination: str
        A path to the folder where the downloaded file will be saved.
    year: int
        The year of the data to download.
    format: str, optional
        Either 'industry by industry' or 'product by product'.
    sut: Boolean, optional 
        If True, also downloads the supply and use tables, otherwise only the input-output matrix.
    headless: Boolean, optional
        If True, runs the browser in headless mode (no GUI). Default is True.
    """
    
    # Check if year is valid
    if not isinstance(year, int) or year < 2010 or year > 2023:
        raise ValueError("As of August 2025, the Figaro database contains IO tables for the years 2010 to 2023. Please provide a valid year within this range."
                         "If you are sure that the year 2024 is already available, please update this check accordingly.")
    
    # Check if destination exists
    if not os.path.exists(destination):
        raise FileNotFoundError(f"The destination folder '{destination}' does not exist. Please create it before downloading.")

    if format == 'industry by industry':
        format_abbr = "ind-by-ind"
    elif format == 'product by product':
        format_abbr = "prod-by-prod"
    else:
        raise ValueError("The 'format' parameter must be either 'industry by industry' or 'product by product'.")
    
    # Check if files already exist
    paths = {
        "io_path" : os.path.join(destination, f"matrix_eu-ic-io_{format_abbr}_25ed_{year}.csv"),
        "sup_path" : os.path.join(destination, f"matrix_eu-ic-supply_25ed_{year}.csv"),
        "use_path" : os.path.join(destination, f"matrix_eu-ic-use_25ed_{year}.csv"), 
        "excel_path" : os.path.join(destination, f"Description_FIGARO_Tables(25ed).xlsx")
    }
    url = "https://circabc.europa.eu/ui/group/cec66924-a924-4f91-a0ef-600a0531e3ba/library/0d8bab1e-d159-40b9-9aff-ef8e6d58e24e?p=1&n=10&sort=name_ASC"

    if any(not os.path.exists(p) for p in paths.values()):
        
        driver = get_driver(destination, headless=headless, prefer="chrome")
        driver.get(url)
        driver.implicitly_wait(5) 
        
        if not os.path.exists(paths["excel_path"]):
            log.info("Downloading the description of the Figaro tables")
            # Find and click the Excel file
            safe_click(driver, By.XPATH, "//a[contains(text(), 'Description_FIGARO_Tables(25ed).xlsx')]", "Excel file link")
            
            # Find and click the download button
            safe_click(driver, By.CSS_SELECTOR, ".download", "Download button for Excel file")
            
            # Wait for the download to complete
            wait_for_download(paths["excel_path"])
            
            # Go back to the main page
            driver.get(url)
        else:
            log.info(f"The description of the Figaro tables is already in the folder '{destination}', skipping download")
        
        if not os.path.exists(paths["io_path"]):
            log.info(f"Downloading IO table for format '{format_abbr}' and year '{year}'")
            # Find and click the desired format (ixi or pxp)
            safe_click(driver, By.XPATH, f"//a[contains(text(), '{format}')]", f"format '{format}' link")

            # Find and click the CSV matrix format
            safe_click(driver, By.XPATH, "//a[contains(text(), 'CSV matrix format')]", "CSV matrix format link")

            # Click for the second page if year > 2019
            if year > 2019:
                time.sleep(0.5) # we need an explicit wait here, because the element is found before it is clickable
                safe_click(driver, By.CLASS_NAME, "next-page", "Next page button")

            # Find and click the desired year
            safe_click(driver, By.XPATH, f"//a[contains(text(), '_{year}.csv')]", f"Year '{year}' link")

            # Find and click the download button
            safe_click(driver, By.CSS_SELECTOR, ".download", "Download button for IO table")

            # Wait for the download to complete
            wait_for_download(paths["io_path"])
            driver.get(url)
        else:
            log.info(f"The IO tables for format '{format}' and year '{year}' are already in the folder '{destination}', skipping download")

        if sut == True: 
            if not os.path.exists(paths["sup_path"]):
                log.info(f"Downloading supply table for year '{year}'")
                # Find and click the supply table
                safe_click(driver, By.XPATH, f"//a[contains(text(), 'Supply tables')]", "Supply tables link")

                # Find and click the CSV matrix format
                safe_click(driver, By.XPATH, "//a[contains(text(), 'CSV matrix format')]", "CSV matrix format link")

                # Click for the second page if year > 2019
                if year > 2019:
                    time.sleep(0.5) 
                    safe_click(driver, By.CLASS_NAME, "next-page", "Next page button")

                # Find and click the desired year
                safe_click(driver, By.XPATH, f"//a[contains(text(), '_{year}.csv')]", f"Year '{year}' link")

                # Find and click the download button
                safe_click(driver, By.CSS_SELECTOR, ".download", "Download button for supply table")

                wait_for_download(paths["sup_path"])
                driver.get(url)
            else: 
                log.info(f"The use tables for year '{year}' are already in the folder '{destination}', skipping download")

            if not os.path.exists(paths["use_path"]):
                log.info(f"Downloading supply table for year '{year}'")

                # Find and click the supply table
                safe_click(driver, By.XPATH, f"//a[contains(text(), 'Use tables')]", "Use tables link")

                # Find and click the CSV matrix format
                safe_click(driver, By.XPATH, "//a[contains(text(), 'CSV matrix format')]", "CSV matrix format link")

                # Click for the second page if year > 2019
                if year > 2019:
                    time.sleep(0.5)
                    safe_click(driver, By.CLASS_NAME, "next-page", "Next page button")

                # Find and click the desired year
                safe_click(driver, By.XPATH, f"//a[contains(text(), '_{year}.csv')]", f"Year '{year}' link")

                # Find and click the download button
                safe_click(driver, By.CSS_SELECTOR, ".download", "Download button for use table")
                wait_for_download(paths["use_path"])
            else:
                log.info(f"The use tables for year '{year}' are already in the folder '{destination}', skipping download")
        driver.quit()
    else:
        log.info(f"The files for format '{format_abbr}' and year '{year}' are already in the folder '{destination}', skipping download")