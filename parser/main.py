
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from parser.driver import SeleniumDriver

class MapsSession:
    def __init__(self, timeout=5, showBrowser=False, userDataDir: str = None):
        self.timeout = timeout
        self.driver = SeleniumDriver(timeout=timeout, showBrowser=showBrowser, userDataDir=userDataDir)
        self.actions = ActionChains(self.driver)

    def wait(self, seconds):
        time.sleep(seconds)

    def close(self):
        self.driver.exit()

    def mouseClick(self, element):
        self.actions.move_to_element(element).click().perform()
    
    def whileClick(self, element):
        while True:
            try:
                element.click()
                break
            except: pass

    def removeElement(self, element):
        self.driver.execute_script("arguments[0].remove();", element)

    def pressHome(self):
        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.HOME)
        self.wait(0.4)

    def setSearchPage(self, text):
        self.driver.get(f'https://yandex.ru/maps/37/astrahan/search/{text}')
        self.wait(0.3)
        self.closeStartBanner()

    def closeStartBanner(self):
        def getAdBannerList():
            return self.driver.findXPathElement("//span[contains(@class, 'je45702c0') and contains(@class, 'ee5069424') and contains(@class, 'bf45a541c') and contains(@class, 'y5a794aea')]", wait=False)

        adBannerList = getAdBannerList()
        if adBannerList is not None: adBannerList.click()

    def setSearchBusPage(self, name):
        self.setSearchPage(f'bus_{name}')
    
    def getBusStopLocations(self, busName):
        def getExpandButton():
            return self.driver.findXPathElement("//div[contains(@class, 'masstransit-legend-group-view__open-button')]")

        def getChangeDirectionButton():
            return self.driver.findXPathElement("//div[contains(@class, 'masstransit-card-header-view__another-threads')]", wait=False)

        def getDestinationButtons():
            return self.driver.findXPathElements("//li[contains(@class, 'masstransit-threads-view__item')]")

        def getBusStopListElement():
            return self.driver.findXPathElement("//ul[contains(@class, 'masstransit-legend-view__legend') and contains(@class, '_type_bus')]")

        def getBusStopElements(busStopListElement):
            while True:
                busStopElements = self.driver.findXPathElements(parent=busStopListElement, value=".//li[contains(@class, 'masstransit-legend-group-view__item')]")
                busStopTextList = [element.text for element in busStopElements]
                if '' not in busStopTextList: break
            return busStopElements

        def getShareButton():
            return self.driver.findXPathElement("//div[contains(@class, 'action-button-view') and contains(@class, '_type_share')]")

        def getLocationElement():
            while True:
                locationElement = self.driver.findXPathElement("//div[contains(@class, 'card-feature-view') and contains(@class, '_view_normal') and contains(@class, '_size_large') and contains(@class, 'card-share-view__coordinates')]")
                if locationElement.text != '': break
            return locationElement

        def getCloseLocationButton():
            return self.driver.findXPathElement("//button[contains(@class, 'close-button') and contains(@class, '_color_additional') and contains(@class, '_circle') and contains(@class, '_relative') and contains(@class, '_size_medium') and contains(@class, '_offset_small')]", wait=False)

        self.setSearchBusPage(busName)
        expandButton = getExpandButton()
        expandButton.click()
        changeDirectionButton = getChangeDirectionButton()
        if changeDirectionButton:
            self.mouseClick(changeDirectionButton)
            destinationButtons = getDestinationButtons()
            directionCount = len(destinationButtons)
            # directionCount = 2
        else:
            directionCount = 1
        busStopLocations = {}
        for directionIndex in range(directionCount):
            if changeDirectionButton:
                destinationButtons = getDestinationButtons()
                self.whileClick(destinationButtons[directionIndex])
            busStopLocations[directionIndex] = {}
            busStopListElement = getBusStopListElement()
            busStopElements = getBusStopElements(busStopListElement)
            for busStopIndex in range(len(busStopElements)):
                busStopName = busStopElements[busStopIndex].text
                if busStopName in busStopLocations: continue
                self.mouseClick(busStopElements[busStopIndex])
                shareButton = getShareButton()
                self.whileClick(shareButton)
                locationElement = getLocationElement()
                latitude, longitude = map(float, locationElement.text.split(', '))
                if busStopLocations[directionIndex].keys(): maxIndex = max(busStopLocations[directionIndex].keys()) + 1
                else: maxIndex = 0
                busStopLocations[directionIndex][maxIndex] = dict(name=busStopName, location=dict(latidude=latitude, longitude=longitude))
                print(directionIndex, maxIndex, busStopLocations[directionIndex][maxIndex])
                self.driver.back()
                closeLocationButton = getCloseLocationButton()
                if closeLocationButton is not None: closeLocationButton.click()
                expandButton = getExpandButton()
                expandButton.click()
                busStopListElement = getBusStopListElement()
                busStopElements = getBusStopElements(busStopListElement)
        return busStopLocations

    def getBusArrivalTimes(self, busName):
        def getChangeDirectionButton():
            return self.driver.findXPathElement("//div[contains(@class, 'masstransit-card-header-view__another-threads')]", wait=False)
        
        def getDestinationButtons():
            return self.driver.findXPathElements("//li[contains(@class, 'masstransit-threads-view__item')]")

        def getBusStopsAndScheduleButtonsElement():
            return self.driver.findXPathElement("//div[contains(@class, 'tabs-select-view__titles')]")

        def getBusStopsAndScheduleButtons(busStopsAndScheduleButtonsElement):
            return self.driver.findXPathElements(parent=busStopsAndScheduleButtonsElement, value=".//div[contains(@class, 'carousel__item') and contains(@class, '_align_center')]")

        def getCalendarButton():
            return self.driver.findXPathElement("//div[contains(@class, 'masstransit-timetable-view__action-button') and contains(@class, '_type_date')]")

        def getWeekElementList():
            return self.driver.findXPathElements("//div[contains(@class, 'react-datepicker__week')]")

        def getDayButtons(weekElement):
            return self.driver.findXPathElements(parent=weekElement, value=".//div[contains(@class, 'react-datepicker__day')]")
        
        def getSelectBusStopButton():
            return self.driver.findXPathElement("//div[contains(@class, 'masstransit-timetable-view__action-button') and contains(@class, '_type_stop')]")

        def getBusStopButtons():
            return self.driver.findXPathElements("//div[contains(@class, 'masstransit-stop-selector-view__snippet') and contains(@role, 'button')]")
        
        def getConfirmButton():
            return self.driver.findXPathElement("//button[contains(@class, 'button') and contains(@class, '_view_primary') and contains(@class, '_ui') and contains(@class, '_size_small')]")

        def getArrivalTimeElements():
            return self.driver.findXPathElements("//li[contains(@class, 'masstransit-vehicle-snippet-view') and contains(@class, '_type_bus')]")

        def getArrivalTimeTextElement(arrivalTimeElement):
            return self.driver.findXPathElement(parent=arrivalTimeElement, value=".//div[contains(@class, 'masstransit-timetable-view__time')]")

        self.setSearchBusPage(busName)
        changeDirectionButton = getChangeDirectionButton()
        if changeDirectionButton:
            self.mouseClick(changeDirectionButton)
            destinationButtons = getDestinationButtons()
            directionCount = len(destinationButtons)
            directionCount = 2
        else:
            directionCount = 1
        if busName == 'М2': startddd, endddd = 1, directionCount + 1
        else: startddd, endddd = 0, directionCount
        busDict = {'week': [{'direction': {num: [] for num in range(directionCount)}}] * 5 + [{'direction': {num: [] for num in range(directionCount)}}] * 2}
        for directionIndex in range(startddd, endddd):
            if changeDirectionButton:
                destinationButtons = getDestinationButtons()
                self.whileClick(destinationButtons[directionIndex])
            busStopsAndScheduleButtonsElement = getBusStopsAndScheduleButtonsElement()
            busStopsAndScheduleButtons = getBusStopsAndScheduleButtons(busStopsAndScheduleButtonsElement)
            scheduleButton = busStopsAndScheduleButtons[1]
            scheduleButton.click()
            for dayIndex in [0, 5]:
                calendarButton = getCalendarButton()
                calendarButton.click()
                weekElementList = getWeekElementList()
                weekElement = weekElementList[3]
                dayButtons = getDayButtons(weekElement)
                dayButtons[dayIndex].click()
                selectBusStopButton = getSelectBusStopButton()
                selectBusStopButton.click()
                self.pressHome()
                busStopButtons = getBusStopButtons()
                for busStopIndex in range(len(busStopButtons)):
                    self.pressHome()
                    busStopButtons = getBusStopButtons()
                    for i in range(busStopIndex): self.removeElement(busStopButtons[i])
                    busStopName = busStopButtons[busStopIndex].text
                    self.mouseClick(busStopButtons[busStopIndex])
                    confirmButton = getConfirmButton()
                    confirmButton.click()
                    arrivalTimes = []
                    self.wait(1)
                    self.pressHome()
                    while True:
                        arrivalTimeElements = getArrivalTimeElements()
                        if not arrivalTimeElements: break
                        arrivalTimeTextElement = getArrivalTimeTextElement(arrivalTimeElements[0])
                        if arrivalTimeTextElement is None:
                            arrivalTimes = []
                            break
                        arrivalTime = arrivalTimeTextElement.text
                        arrivalTimes.append(arrivalTime)
                        self.removeElement(arrivalTimeElements[0])
                        if len(arrivalTimeElements) == 1: break

                    realDirection = directionIndex if busName != 'М2' else 2 - directionIndex
                    busDict['week'][dayIndex]['direction'][realDirection].append(arrivalTimes)
                    print(busStopName, dayIndex, realDirection, arrivalTimes)
                    selectBusStopButton = getSelectBusStopButton()
                    selectBusStopButton.click()
                    self.wait(0.4)
                confirmButton = getConfirmButton()
                confirmButton.click()
        return busDict