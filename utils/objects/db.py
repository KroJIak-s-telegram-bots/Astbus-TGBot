
class User:
    def __init__(self, userId, dictUser):
        self.userId = userId
        self.login = dictUser['login']
        self.fullname = dictUser['fullname']
        self.permission = dictUser['permission']
        self.removedMessageIds = dictUser['removedMessageIds']
        self.startMessageId = dictUser['startMessageId']
        self.busMessageId = dictUser['busMessageId']
        self.favourites = dictUser['favourites']
        self.usedBuses = dictUser['usedBuses']

    def isDefault(self):
        return self.permission == 'default'

    def isAdmin(self):
        return self.permission == 'admin'

class BusStop:
    def __init__(self, dictBusStop):
        self.directions = {int(key): value for key, value in dictBusStop['directions'].items()}

class Bus:
    def __init__(self, name, dictBus):
        self.name = name
        self.stops = BusStop(dictBus['stops'])
        self.circularRoute = dictBus['circularRoute']

class Location:
    def __init__(self, name, dictLocation):
        self.name = name
        self.latitude = dictLocation['latitude']
        self.longitude = dictLocation['longitude']