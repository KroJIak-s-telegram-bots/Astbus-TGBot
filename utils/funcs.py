
from os.path import join as joinPath
import math
import time

from configparser import ConfigParser

from utils.objects.db import Location

def getConfigObject(botConfigPath):
    config = ConfigParser()
    config.read(botConfigPath)
    return config

def getLocalTime(format):
    localTime = time.localtime()
    match format:
        case 0: return time.strftime('%H:%M:%S', localTime)
        case 1: return time.strftime('%d_%m_%y_%H_%M_%S', localTime)

def getFullLocalTime():
    currentTime = getLocalTime(0)
    hour, minute, second = map(int, currentTime.split(':'))
    fullLocalTime = hour * 3600 + minute * 60 + second
    return fullLocalTime

def getLogFileName():
    localTime = getLocalTime(1)
    resultName = f'log_{localTime}.log'
    return resultName

def getDistanceByHaversine(location1: Location, location2: Location, earthRadius=6371.0):
    # Преобразование градусов в радианы
    latitude1 = math.radians(location1.latitude)
    longitude1 = math.radians(location1.longitude)
    latitude2 = math.radians(location2.latitude)
    longitude2 = math.radians(location2.longitude)
    # Разница координат
    dLatitude = latitude2 - latitude1
    dLongitude = longitude2 - longitude1
    # Формула Haversine
    a = math.sin(dLatitude / 2) ** 2 + math.cos(latitude1) * math.cos(latitude2) * math.sin(dLongitude / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # Расстояние в километрах
    distance = earthRadius * c
    return distance
