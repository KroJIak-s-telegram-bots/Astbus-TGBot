
import json

from parser.main import MapsSession
from utils.const import ConstPlenty
from utils.funcs import joinPath

const = ConstPlenty()
availableBuses = '190;18;45;М6;М4;М1;М5;М2;63;78;М3;37;117;38;4;30;73;28;53;10;33;54с;116;2;90;13;9;54к;19н;58;29;30н;13'
availableBuses = availableBuses.split(';')

def get():
    with open(joinPath(const.path.parser, 'temp.json')) as file:
        dbData = json.load(file)
    return dbData

def save(dbData):
    with open(joinPath(const.path.parser, 'temp.json'), 'w', encoding='utf-8') as file:
        json.dump(dbData, file, indent=4, ensure_ascii=False)

def saveBusStopLocations():
    dbData = get()
    session = MapsSession(showBrowser=True, userDataDir='/home/andrey/PycharmProjects/Astbus-TGBot/cache/web/users')
    for busName in availableBuses:
        busStopLocations = session.getBusStopLocations(busName)
        busStopIndexDict = {}
        for directionIndex, currentLocations in busStopLocations.items():
            busStopIndexList = [-1] * len(currentLocations)
            for listIndex, (busStopIndex1, busStopInfo1) in enumerate(currentLocations.items()):
                for busStopIndex2, busStopInfo2 in dbData['locations'].items():
                    if busStopInfo1 == busStopInfo2:
                        print('SWAP')
                        busStopIndexList[listIndex] = busStopIndex2
                        break
                else:
                    newBusStopIndex = len(dbData['locations'])
                    busStopIndexList[listIndex] = newBusStopIndex
                    dbData['locations'][newBusStopIndex] = busStopInfo1
            for i, busStopIndex in enumerate(busStopIndexList):
                busStopIndexList[i] = {'index': int(busStopIndex), 'times': None}
            busStopIndexDict[directionIndex] = busStopIndexList
        dbData['buses'][busName] = {'week': [{'direction': busStopIndexDict}] * 7}
        save(dbData)
    session.close()

def saveBusArrivalTimes():
    dbData = get()
    session = MapsSession(showBrowser=True, userDataDir='/home/andrey/PycharmProjects/Astbus-TGBot/cache/web/users')
    for busName in availableBuses:
        print(f'\n{busName}\n')
        busDict = session.getBusArrivalTimes(busName)
        for dayIndex, day in enumerate(busDict['week']):
            for directionIndex, busStops in day['direction'].items():
                for busStopIndex in range(len(busStops)):
                    dbData['buses'][busName]['week'][dayIndex]['direction'][str(directionIndex)][busStopIndex]['times'] = busStops[busStopIndex]
        save(dbData)
    session.close()

def main():
    saveBusStopLocations()
    saveBusArrivalTimes()

if __name__ == '__main__':
    main()