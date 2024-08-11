
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

class WayPoint:
    def __init__(self, dictWayPoint):
        self.index = dictWayPoint['index']
        self.times = dictWayPoint['times']

class Location:
    def __init__(self, dictLocation):
        self.latitude = dictLocation['latitude']
        self.longitude = dictLocation['longitude']

class BusStop:
    def __init__(self, index, dictBusStop):
        self.index = index
        self.name = dictBusStop['name']
        self.location = Location(dictBusStop['location'])

