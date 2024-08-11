
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent

class SeleniumDriver(webdriver.Chrome):
    def __init__(self, timeout, addfakeUserAgent=True, showBrowser=True, windowSize=(1920, 1080), userDataDir: str = None):
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument('--disable-blink-features=AutomationControlled')
        chromeOptions.add_argument('disable-infobars')
        if addfakeUserAgent:
            chromeOptions.add_argument(f'user-agent={UserAgent().chrome}')
        if not showBrowser:
            chromeOptions.add_argument('--headless')
        if userDataDir:
            chromeOptions.add_argument(f'--user-data-dir={userDataDir}')
        super().__init__(options=chromeOptions)
        self.timeout = timeout
        self.windowSize = windowSize
        self.setDefaultSettings()

    def setDefaultSettings(self):
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                          const newProto = navigator.proto
                          delete newProto.parse
                          navigator.proto = newProto
                          """
        })
        self.set_window_size(*self.windowSize)

    def findXPathElement(self, value, parent=None, wait=True):
        timer = time.time() + self.timeout
        while True:
            try:
                if parent is None: element = self.find_element(By.XPATH, value)
                else: element = parent.find_element(By.XPATH, value)
                break
            except:
                pass
            if not wait or timer < time.time():
                return None
        return element
    
    def findXPathElements(self, value, parent=None, wait=True):
        timer = time.time() + self.timeout
        while True:
            if parent is None: elements = self.find_elements(By.XPATH, value)
            else: elements = parent.find_elements(By.XPATH, value)
            if not wait or elements or timer < time.time():
                break
        return elements
    
    def exit(self):
        self.close()