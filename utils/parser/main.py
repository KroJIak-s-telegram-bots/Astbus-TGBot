
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from utils.parser.driver import SeleniumDriver

class MapsSession:
    def __init__(self, timeout=3, showBrowser=False, userDataDir: str = None):
        self.timeout = timeout
        self.driver = SeleniumDriver(showBrowser=showBrowser, userDataDir=userDataDir)
        self.actions = ActionChains(self.driver)

    def click(self, object):
        self.actions.move_to_element(object).click().perform()

    def setSearchPage(self, text):
        self.driver.get(f'https://yandex.ru/maps/37/astrahan/search/{text}')
        self.wait(0.1)
        self.closeStartBanner()

    def closeStartBanner(self):
        startTime = time.time()
        while True:
            startBannerList = self.driver.find_elements(By.XPATH,"//span[contains(@class, 'je45702c0') and contains(@class, 'ee5069424') "
                                                                 "and contains(@class, 'bf45a541c') and contains(@class, 'y5a794aea')]")
            sidePanelList = self.driver.find_elements(By.XPATH, "//span[contains(@class, 'input__context')]")
            if startBannerList:
                print("STARTBANNER")
                break
            if sidePanelList or startTime + self.timeout < time.time():
                print('SIDEPANEL')
                return
        startBanner = startBannerList[0]
        self.click(startBanner)

    def setSearchBusPage(self, name):
        self.setSearchPage(f'bus_{name}')

    def getBusStopNames(self, busName):
        self.setSearchBusPage(busName)
        self.wait(0.5)
        expandButton = self.driver.find_element(By.XPATH, "//div[contains(@class, 'masstransit-legend-group-view__open-button')]")
        self.click(expandButton)
        self.wait(1)
        busStopNames = {'directions': {}}
        changeDirectionButtonList = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'masstransit-card-header-view__another-threads')]")
        if len(changeDirectionButtonList) == 0:
            circularRoute = True
            busStopNamesObject = self.driver.find_element(By.XPATH, "//ul[contains(@class, 'masstransit-legend-view__legend') and contains(@class, '_type_bus')]")
            busStopNamesBothDirections = busStopNamesObject.text.replace('Свернуть\n', '').split('\n')
            lastBusStopName, separateIndex = None, None
            for i, bsn in enumerate(busStopNamesBothDirections):
                if bsn == lastBusStopName:
                    separateIndex = i
                    break
            busStopNames['directions'][0] = busStopNamesBothDirections[:separateIndex]
            busStopNames['directions'][1] = busStopNamesBothDirections[separateIndex:]
        else:
            circularRoute = False
            changeDirectionButton = changeDirectionButtonList[0]
            self.click(changeDirectionButton)
            for index in range(2):
                destinationButtons = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'masstransit-threads-view__item')]")
                self.click(destinationButtons[index])
                busStopNamesObject = self.driver.find_element(By.XPATH, "//ul[contains(@class, 'masstransit-legend-view__legend') and contains(@class, '_type_bus')]")
                busStopNamesThisDirection = busStopNamesObject.text.replace('Свернуть\n', '').split('\n')
                busStopNames['directions'][index] = busStopNamesThisDirection
        return busStopNames, circularRoute

    def getBusStopLocations(self, busName):
        self.setSearchBusPage(busName)
        self.wait(0.7)
        expandButton = self.driver.find_element(By.XPATH, "//div[contains(@class, 'masstransit-legend-group-view__open-button')]")
        self.click(expandButton)
        self.wait(1)
        busStopLocations = {}
        changeDirectionButtonList = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'masstransit-card-header-view__another-threads')]")
        if changeDirectionButtonList:
            changeDirectionButton = changeDirectionButtonList[0]
            self.click(changeDirectionButton)
        for index in range(2):
            if changeDirectionButtonList:
                destinationButtons = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'masstransit-threads-view__item')]")
                self.click(destinationButtons[index])
            busStopNamesObject = self.driver.find_element(By.XPATH, "//ul[contains(@class, 'masstransit-legend-view__legend') and contains(@class, '_type_bus')]")
            busStopObjects = busStopNamesObject.find_elements(By.XPATH, ".//li[contains(@class, 'masstransit-legend-group-view__item')]")
            for index in range(len(busStopObjects)):
                busStopName = busStopObjects[index].text
                if busStopName in busStopLocations: continue
                self.click(busStopObjects[index])
                self.wait(4)
                shareButton = self.driver.find_element(By.XPATH, "//div[contains(@class, 'action-button-view') and contains(@class, '_type_share')]")
                self.click(shareButton)
                self.wait(1)
                locationObject = self.driver.find_element(By.XPATH, "//div[contains(@class, 'card-feature-view') and contains(@class, '_view_normal') and contains(@class, '_size_large') and contains(@class, 'card-share-view__coordinates')]")
                locationText = locationObject.text
                latitude, longitude = locationText.split(', ')
                latitude, longitude = float(latitude), float(longitude)
                location = {'latitude': latitude, 'longitude': longitude}
                busStopLocations[busStopName] = location
                self.driver.back()
                self.wait(3)
                expandButton = self.driver.find_element(By.XPATH, "//div[contains(@class, 'masstransit-legend-group-view__open-button')]")
                self.click(expandButton)
                self.wait(1)
                busStopNamesObject = self.driver.find_element(By.XPATH, "//ul[contains(@class, 'masstransit-legend-view__legend') and contains(@class, '_type_bus')]")
                busStopObjects = busStopNamesObject.find_elements(By.XPATH, ".//li[contains(@class, 'masstransit-legend-group-view__item')]")
                while '' in [nnnn.text for nnnn in busStopObjects]:
                    busStopObjects = busStopNamesObject.find_elements(By.XPATH, ".//li[contains(@class, 'masstransit-legend-group-view__item')]")
            if not changeDirectionButtonList: break
        return busStopLocations

    def getBusArrivalTimes(self, bus, direction, busStopName):
        self.setSearchBusPage(bus.name)
        self.wait(0.5)
        if not bus.circularRoute:
            changeDirectionButton = self.driver.find_element(By.XPATH, "//div[contains(@class, 'masstransit-card-header-view__another-threads')]")
            self.click(changeDirectionButton)
            destinationButtons = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'masstransit-threads-view__item')]")
            self.click(destinationButtons[direction])
        busStopsAndScheduleButtonsObject = self.driver.find_element(By.XPATH, "//div[contains(@class, 'tabs-select-view__titles')]")
        busStopsAndScheduleButtons = busStopsAndScheduleButtonsObject.find_elements(By.XPATH, ".//div[contains(@class, 'carousel__item') and contains(@class, '_align_center')]")
        scheduleButton = busStopsAndScheduleButtons[1]
        self.click(scheduleButton)
        self.wait(0.5)
        selectBusStopButton = self.driver.find_element(By.XPATH, "//div[contains(@class, 'masstransit-timetable-view__action-button') and contains(@class, '_type_stop')]")
        self.click(selectBusStopButton)
        busStopButtons = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'masstransit-stop-selector-view__snippet') and contains(@role, 'button')]")
        for index, bsb in enumerate(busStopButtons):
            if busStopName == bsb.text: break
            else: self.driver.execute_script("arguments[0].remove();", bsb)
        else: return None
        busStopButtons = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'masstransit-stop-selector-view__name')]")
        self.click(busStopButtons[0])
        self.wait(0.5)
        confirmButton = self.driver.find_element(By.XPATH, "//button[contains(@class, 'button') and contains(@class, '_view_primary') and contains(@class, '_ui') and contains(@class, '_size_small')]")
        self.click(confirmButton)
        self.wait(1.5)
        arrivalTimeObjects = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'masstransit-timetable-view__time')]")
        if not arrivalTimeObjects: return []
        arrivalTimes = [object.text for object in arrivalTimeObjects]
        return arrivalTimes

    def wait(self, seconds):
        time.sleep(seconds)

    def close(self):
        self.driver.exit()

def test():
    class Bus:
        def __init__(self, name, circularRoute):
            self.name = name
            self.circularRoute = circularRoute

    session = MapsSession(showBrowser=False, userDataDir='/home/andrey/PycharmProjects/Astbus-TGBot/cache/web/users')
    bus = Bus('190', False)
    nearestBusStopName = 'ТЦ Ярмарка'
    direction = 0
    busArrivalTimes = session.getBusArrivalTimes(bus, direction, nearestBusStopName)
    print(busArrivalTimes)

if __name__ == '__main__':
    test()