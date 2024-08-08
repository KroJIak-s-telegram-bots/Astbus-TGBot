
import json
import os

from utils.funcs import joinPath
from utils.const import ConstPlenty
from utils.objects.db import User, Bus, Location

const = ConstPlenty()

class dbWorker():
    def __init__(self, databasePath):
        folderPath = databasePath.split('/')
        self.fileName = folderPath.pop(-1)
        self.folderPath = '/'.join(folderPath)
        if not self.isExists(): self.save({})

    def isExists(self):
        files = os.listdir(self.folderPath if len(self.folderPath) > 0 else None)
        return self.fileName in files

    def get(self):
        with open(joinPath(self.folderPath, self.fileName)) as file:
            dbData = json.load(file)
        return dbData

    def save(self, dbData):
        with open(joinPath(self.folderPath, self.fileName), 'w', encoding='utf-8') as file:
            json.dump(dbData, file, indent=4, ensure_ascii=False)

class dbLocalWorker():
    def __init__(self):
        self.db = {}

    def isUserExists(self, userId):
        return str(userId) in self.db

    def addNewUser(self, userId):
        self.db[str(userId)] = dict(mode=-1,
                                    currentBus=None,
                                    currentDirection=None)

    def setUserMode(self, userId, mode):
        self.db[str(userId)]['mode'] = mode

    def getUserMode(self, userId):
        return self.db[str(userId)]['mode']

    def setCurrentBus(self, userId, name):
        self.db[str(userId)]['currentBus'] = name

    def getCurrentBus(self, userId):
        return self.db[str(userId)]['currentBus']

    def setCurrentDirection(self, userId, index):
        self.db[str(userId)]['currentDirection'] = index

    def getCurrentDirection(self, userId):
        return self.db[str(userId)]['currentDirection']

class dbUsersWorker(dbWorker):
    def getUserIds(self):
        dbData = self.get()
        userIds = tuple(dbData['users'].keys())
        return userIds

    def isUserExists(self, userId):
        dbData = self.get()
        return str(userId) in dbData['users']

    def addNewUser(self, userId, login, fullname, permission):
        dbData = self.get()
        newUser = dict(login=login,
                       fullname=fullname,
                       permission=permission,
                       removedMessageIds=[],
                       startMessageId=None,
                       busMessageId=None,
                       favourites=[],
                       usedBuses={})
        dbData['users'][str(userId)] = newUser
        self.save(dbData)

    def getUser(self, userId):
        dbData = self.get()
        dictUser = dbData['users'][str(userId)]
        user = User(str(userId), dictUser)
        return user

    def addRemovedMessageIds(self, userId, messageId):
        dbData = self.get()
        removedMessageIds = set(dbData['users'][str(userId)]['removedMessageIds'])
        removedMessageIds.add(messageId)
        dbData['users'][str(userId)]['removedMessageIds'] = list(removedMessageIds)
        self.save(dbData)

    def clearRemovedMessageIds(self, userId):
        dbData = self.get()
        dbData['users'][str(userId)]['removedMessageIds'] = []
        self.save(dbData)

    def setBusMessageId(self, userId, messageId):
        dbData = self.get()
        dbData['users'][str(userId)]['busMessageId'] = messageId
        self.save(dbData)

    def setStartMessageId(self, userId, messageId):
        dbData = self.get()
        dbData['users'][str(userId)]['startMessageId'] = messageId
        self.save(dbData)

    def addToFavourites(self, userId, name):
        dbData = self.get()
        dbData['users'][str(userId)]['favourites'].append(name)
        self.save(dbData)

    def removeFromFavourites(self, userId, name):
        dbData = self.get()
        favouritesList = dbData['users'][str(userId)]['favourites']
        index = favouritesList.index(name)
        dbData['users'][str(userId)]['favourites'].pop(index)
        self.save(dbData)

    def addUsedBus(self, userId, name):
        dbData = self.get()
        usedBusesList = dbData['users'][str(userId)]['usedBuses']
        if name not in usedBusesList:
            dbData['users'][str(userId)]['usedBuses'][name] = 1
        else:
            dbData['users'][str(userId)]['usedBuses'][name] += 1
        self.save(dbData)

    def getPermissions(self):
        dbData = self.get()
        permissions = tuple(dbData['permissions'].values())
        return permissions

class dbMovesWorker(dbWorker):
    def getAllBuses(self):
        dbData = self.get()
        buses = [Bus(name, dictBus) for name, dictBus in dbData['buses'].items()]
        return buses

    def getBus(self, name):
        dbData = self.get()
        dictBus = dbData['buses'][name]
        bus = Bus(name, dictBus)
        return bus

    def getAllLocations(self):
        dbData = self.get()
        locations = [Location(name, dictLocation) for name, dictLocation in dbData['locations'].items()]
        return locations

    def getLocation(self, name):
        dbData = self.get()
        dictLocation = dbData['locations'][name]
        location = Location(name, dictLocation)
        return location