
import json

from utils.parser.main import MapsSession
from utils.const import ConstPlenty
from utils.funcs import joinPath

const = ConstPlenty()
availableBuses = '190;18;45;М6;М4;М1;М5;М2;63;78;М3;37;117;38;4;30;73;28;53;10;33;54с;116;2;90;13;9;54к;19н;58;29;30н;13'
availableBuses = availableBuses.split(';')

def get():
    with open(joinPath(const.path.parser, 'database.json')) as file:
        dbData = json.load(file)
    return dbData

def save(dbData):
    with open(joinPath(const.path.parser, 'database.json'), 'w', encoding='utf-8') as file:
        json.dump(dbData, file, indent=4, ensure_ascii=False)

def saveBusRoutes():
    dbData = get()
    session = MapsSession(showBrowser=True, userDataDir=f'{const.path.userData}')
    for busName in availableBuses:
        busStopNames, circularRoute = session.getBusStopNames(busName)
        print(busName, circularRoute, busStopNames)
        dbData['buses'][busName] = {'stops': busStopNames, 'circularRoute': circularRoute}
        save(dbData)
    session.close()

def saveBusStopLocations():
    dbData = get()
    session = MapsSession(showBrowser=True, userDataDir=f'{const.path.userData}')
    for busName in availableBuses:
        busStopLocations = session.getBusStopLocations(busName)
        for bsn, location in busStopLocations.items():
            print(busName, bsn, location)
            if bsn not in dbData['locations']:
                dbData['locations'][bsn] = location
                save(dbData)
    session.close()

def main():
    saveBusRoutes()
    saveBusStopLocations()

if __name__ == '__main__':
    main()