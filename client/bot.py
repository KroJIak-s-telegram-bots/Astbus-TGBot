
from traceback import format_exc
import asyncio
import logging
import json
import shutil

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram import F

from utils.const import ConstPlenty
from utils.funcs import joinPath, getConfigObject, getLogFileName, getDistanceByHaversine
from utils.database import dbUsersWorker, dbMovesWorker, dbLocalWorker
from utils.objects.client import UserInfo, CallbackUserInfo
from utils.parser.main import MapsSession

const = ConstPlenty()
botConfig = getConfigObject(joinPath(const.path.config, const.file.config))
const.addConstFromConfig(botConfig)
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO, filename=joinPath(const.path.logs, getLogFileName()), filemode='w', format=const.logging.format)
dbUsers = dbUsersWorker(joinPath(const.path.users, const.file.database))
dbMoves = dbMovesWorker(joinPath(const.path.moves, const.file.database))
dbLocal = dbLocalWorker()
bot = Bot(const.telegram.token, default=DefaultBotProperties(parse_mode=const.default.parseMode))
dp = Dispatcher()

def getTranslation(userInfo, key, inserts=[]):
    user = dbUsers.getUser(userInfo.userId)
    try:
        with open(joinPath(const.path.lang, f'{const.data.defaultLang}.json'), encoding='utf-8') as langFile:
            langJson = json.load(langFile)
        text = langJson[key]
        if not inserts: return text
        for ins in inserts: text = text.replace('%{}%', str(ins), 1)
        return text
    except Exception:
        if user.isAdmin(): return getTranslation(userInfo, 'error.message', [format_exc()])
        else: return getTranslation(userInfo, 'error.message', ['wwc'])

def getUserInfo(message=None, callback=None, addRemovedMessage=True):
    if message is None and callback is None: raise ValueError('No message or callback.')
    userInfo = UserInfo(message) if message else CallbackUserInfo(callback)
    if not dbUsers.isUserExists(userInfo.userId):
        permissions = dbUsers.getPermissions()
        dbUsers.addNewUser(userInfo.userId, userInfo.username, userInfo.userFullName, permissions[0])
    if not dbLocal.isUserExists(userInfo.userId):
        dbLocal.addNewUser(userInfo.userId)
    if addRemovedMessage and message: dbUsers.addRemovedMessageIds(userInfo.userId, userInfo.messageId)
    userLogInfo = f'{userInfo} | {dbLocal.db[str(userInfo.userId)]}'
    logging.info(userLogInfo)
    print(userLogInfo)
    return userInfo

async def removeLastMessageIds(userInfo):
    user = dbUsers.getUser(userInfo.userId)
    for messageId in user.removedMessageIds:
        try: await bot.delete_message(userInfo.chatId, messageId)
        except: pass
    dbUsers.clearRemovedMessageIds(userInfo.userId)

async def removeBusMessageId(userInfo):
    user = dbUsers.getUser(userInfo.userId)
    if user.busMessageId is None: return
    try: await bot.delete_message(userInfo.chatId, user.busMessageId)
    except: pass
    dbUsers.setBusMessageId(userInfo.userId, None)

async def removeStartMessageId(userInfo):
    user = dbUsers.getUser(userInfo.userId)
    if user.startMessageId is None: return
    try: await bot.delete_message(userInfo.chatId, user.startMessageId)
    except: pass
    dbUsers.setStartMessageId(userInfo.userId, None)

def getMainKeyboard(userInfo):
    user = dbUsers.getUser(userInfo.userId)
    aboutButton = [types.KeyboardButton(text=getTranslation(userInfo, 'button.about'))]
    busButton = [types.KeyboardButton(text=getTranslation(userInfo, 'button.buses'))]
    favouritesButton = [types.KeyboardButton(text=getTranslation(userInfo, 'button.favourites'))]
    lastUsedBuses = sorted(user.usedBuses.items(), key=lambda bus: bus[1], reverse=True)
    lastUsedBusNames = [bus[0] for bus in lastUsedBuses]
    lastUsedBusNames = lastUsedBusNames[:3]
    lastUsedBusButtons = [types.KeyboardButton(text=name) for name in lastUsedBusNames]
    keyboardList = [aboutButton, busButton + favouritesButton, lastUsedBusButtons]
    replyKeyboard = types.ReplyKeyboardMarkup(keyboard=keyboardList, resize_keyboard=True, input_field_placeholder=getTranslation(userInfo, 'inputfield.message'))
    return replyKeyboard

def isAboutCommand(userInfo):
    return userInfo.userText.lower() == getTranslation(userInfo, 'button.about').lower()

@dp.message(Command('start'))
async def startHandler(message: types.Message):
    userInfo = getUserInfo(message=message)
    await removeLastMessageIds(userInfo)
    await removeBusMessageId(userInfo)
    mainKeyboard = getMainKeyboard(userInfo)
    botMessage = await message.answer(getTranslation(userInfo, 'start.message', [userInfo.userFirstName]), reply_markup=mainKeyboard)
    await removeStartMessageId(userInfo)
    dbUsers.setStartMessageId(userInfo.userId, botMessage.message_id)

def clearTextForBusName(text):
    return text.replace(' ', '').lower().replace('m', 'м').replace('k', 'к').replace('c', 'с').replace('h', 'н')

def getCorrectBusName(name):
    for correctName in const.data.availableBuses:
        if clearTextForBusName(name) == clearTextForBusName(correctName):
            return correctName
    return None

@dp.callback_query(F.data.startswith(const.callback.prefix.bus + '_'))
async def chooseBusHandler(callback: types.CallbackQuery):
    userInfo = getUserInfo(callback=callback)
    busName = userInfo.action.split('_')[1]
    await chooseDirectionBusHandler(userInfo, busName)

def getDirectionKeyboard(userInfo, direction):
    confirmButton = [types.InlineKeyboardButton(text=getTranslation(userInfo, 'button.choose'), callback_data=f'{const.callback.prefix.direction}_{direction}')]
    keyboardList = [confirmButton]
    inlineKeyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboardList)
    return inlineKeyboard

async def chooseDirectionBusHandler(userInfo, busName):
    dbLocal.setCurrentBus(userInfo.userId, busName)
    await removeLastMessageIds(userInfo)
    await removeBusMessageId(userInfo)
    dbUsers.addUsedBus(userInfo.userId, busName)
    bus = dbMoves.getBus(busName)
    botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'bus.message.direction', [busName]))
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)
    for direction in range(2):
        busStops = bus.stops.directions[direction]
        startStop, middleStop, endStop = busStops[0], busStops[len(busStops) // 2], busStops[-1]
        directionText = f'<b>{startStop}</b> -> ... -> <b>{middleStop}</b> -> ... -> <b>{endStop}</b>'
        directionKeyboard = getDirectionKeyboard(userInfo, direction)
        botMessage = await bot.send_message(userInfo.chatId, directionText, reply_markup=directionKeyboard)
        dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)

@dp.callback_query(F.data.startswith(const.callback.prefix.direction + '_'))
async def directionHandler(callback: types.CallbackQuery):
    userInfo = getUserInfo(callback=callback)
    await removeLastMessageIds(userInfo)
    direction = int(userInfo.action.split('_')[1])
    dbLocal.setCurrentDirection(userInfo.userId, direction)
    await busHandler(userInfo)

def getBusKeyboard(userInfo, busName):
    user = dbUsers.getUser(userInfo.userId)
    if busName in user.favourites:
        changeFavouritesButton = [types.InlineKeyboardButton(text=getTranslation(userInfo, 'button.favourites.remove'), callback_data=const.callback.removefavourites)]
    else:
        changeFavouritesButton = [types.InlineKeyboardButton(text=getTranslation(userInfo, 'button.favourites.add'), callback_data=const.callback.addfavourites)]
    sendLocationButton = [types.InlineKeyboardButton(text=getTranslation(userInfo, 'button.location'), callback_data=const.callback.location)]
    selectBusStopButton = [types.InlineKeyboardButton(text=getTranslation(userInfo, 'button.busstop'), callback_data=const.callback.busstop)]
    keyboardList = [changeFavouritesButton, sendLocationButton, selectBusStopButton]
    inlineKeyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboardList)
    return inlineKeyboard

async def busHandler(userInfo):
    busName = dbLocal.getCurrentBus(userInfo.userId)
    busKeyboard = getBusKeyboard(userInfo, busName)
    botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'bus.message.tracking', [busName]), reply_markup=busKeyboard)
    dbUsers.setBusMessageId(userInfo.userId, botMessage.message_id)

@dp.callback_query(F.data == const.callback.addfavourites)
async def addFavouritesHandler(callback: types.CallbackQuery):
    userInfo = getUserInfo(callback=callback)
    currentBusName = dbLocal.getCurrentBus(userInfo.userId)
    dbUsers.addToFavourites(userInfo.userId, currentBusName)
    busKeyboard = getBusKeyboard(userInfo, currentBusName)
    user = dbUsers.getUser(userInfo.userId)
    await bot.edit_message_reply_markup(chat_id=userInfo.chatId, message_id=user.busMessageId, reply_markup=busKeyboard)

@dp.callback_query(F.data == const.callback.removefavourites)
async def removeFavouritesHandler(callback: types.CallbackQuery):
    userInfo = getUserInfo(callback=callback)
    currentBusName = dbLocal.getCurrentBus(userInfo.userId)
    dbUsers.removeFromFavourites(userInfo.userId, currentBusName)
    busKeyboard = getBusKeyboard(userInfo, currentBusName)
    user = dbUsers.getUser(userInfo.userId)
    await bot.edit_message_reply_markup(chat_id=userInfo.chatId, message_id=user.busMessageId, reply_markup=busKeyboard)

def getBusStopListKeyboard(busStopNames):
    keyboardList = [[types.InlineKeyboardButton(text=name, callback_data=f'{const.callback.prefix.busstop}_{index}')]
                    for index, name in enumerate(busStopNames)]
    inlineKeyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboardList)
    return inlineKeyboard

@dp.callback_query(F.data == const.callback.busstop)
async def busStopListHandler(callback: types.CallbackQuery):
    userInfo = getUserInfo(callback=callback)
    await removeLastMessageIds(userInfo)
    busName = dbLocal.getCurrentBus(userInfo.userId)
    direction = dbLocal.getCurrentDirection(userInfo.userId)
    bus = dbMoves.getBus(busName)
    busStopNames = bus.stops.directions[direction]
    busStopListKeyboard = getBusStopListKeyboard(busStopNames)
    botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'busstoplist.message.available'), reply_markup=busStopListKeyboard)
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)

@dp.callback_query(F.data.startswith(const.callback.prefix.busstop + '_'))
async def selectedBusStopHandler(callback: types.CallbackQuery):
    userInfo = getUserInfo(callback=callback)
    await removeLastMessageIds(userInfo)
    busStopIndex = int(userInfo.action.split('_')[1])
    busName = dbLocal.getCurrentBus(userInfo.userId)
    direction = dbLocal.getCurrentDirection(userInfo.userId)
    bus = dbMoves.getBus(busName)
    busStopNames = bus.stops.directions[direction]
    nearestBusStopName = busStopNames[busStopIndex]
    botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'busstoplist.message.success'))
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)
    await busArrivalTimesHandler(userInfo, nearestBusStopName)

def getLocationKeyboard(userInfo):
    button = [types.KeyboardButton(text=getTranslation(userInfo, 'button.location'), request_location=True)]
    keyboardList = [button]
    replyKeyboard = types.ReplyKeyboardMarkup(keyboard=keyboardList, resize_keyboard=True)
    return replyKeyboard

@dp.callback_query(F.data == const.callback.location)
async def sendLocationHandler(callback: types.CallbackQuery):
    userInfo = getUserInfo(callback=callback)
    await removeLastMessageIds(userInfo)
    locationKeyboard = getLocationKeyboard(userInfo)
    botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'location.message.send'), reply_markup=locationKeyboard)
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)

@dp.message(F.location)
async def locationHandler(message: types.location):
    userInfo = getUserInfo(message=message, addRemovedMessage=False)
    await removeLastMessageIds(userInfo)
    dbUsers.addRemovedMessageIds(userInfo.userId, userInfo.messageId)
    mainKeyboard = getMainKeyboard(userInfo)
    botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'location.message.success'), reply_markup=mainKeyboard)
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)
    
    busName = dbLocal.getCurrentBus(userInfo.userId)
    direction = dbLocal.getCurrentDirection(userInfo.userId)
    bus = dbMoves.getBus(busName)
    nearestBusStopName = getNearestBusStop(bus, direction, message.location)
    await busArrivalTimesHandler(userInfo, nearestBusStopName)

async def busArrivalTimesHandler(userInfo, nearestBusStopName):
    user = dbUsers.getUser(userInfo.userId)
    await bot.edit_message_reply_markup(chat_id=userInfo.chatId, message_id=user.busMessageId, reply_markup=None)
    dbUsers.addRemovedMessageIds(userInfo.userId, user.busMessageId)
    dbUsers.setBusMessageId(userInfo.userId, None)
    busName = dbLocal.getCurrentBus(userInfo.userId)
    direction = dbLocal.getCurrentDirection(userInfo.userId)
    bus = dbMoves.getBus(busName)
    busArrivalTimes = getBusArrivalTimes(userInfo, bus, direction, nearestBusStopName)
    await removeLastMessageIds(userInfo)
    mainKeyboard = getMainKeyboard(userInfo)
    if busArrivalTimes is None:
        botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'arrivaltimes.message.error'), reply_markup=mainKeyboard)
    elif busArrivalTimes:
        busArrivalTimesText = ', '.join([f'<b>{busArrivalTimes[0]}</b>'] + busArrivalTimes[1:])
        botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'arrivaltimes.message.success', [busName, nearestBusStopName, busArrivalTimesText]), reply_markup=mainKeyboard)
        dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)
        busStopLocation = dbMoves.getLocation(nearestBusStopName)
        botMessage = await bot.send_location(userInfo.chatId, latitude=busStopLocation.latitude, longitude=busStopLocation.longitude)
    else:
        botMessage = await bot.send_message(userInfo.chatId, getTranslation(userInfo, 'arrivaltimes.message.empty', [busName, nearestBusStopName]), reply_markup=mainKeyboard)
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)
    dbLocal.setCurrentBus(userInfo.userId, None)
    dbLocal.setCurrentDirection(userInfo.userId, None)

def getBusArrivalTimes(userInfo, bus, direction, nearestBusStopName):
    for attempt in range(10):
        session = MapsSession(showBrowser=False, userDataDir=f'{const.path.userData}-{userInfo.userId}')
        try:
            busArrivalTimes = session.getBusArrivalTimes(bus, direction, nearestBusStopName)
            session.close()
            break
        except Exception:
            session.close()
            logging.error(format_exc())
    else: busArrivalTimes = None
    return busArrivalTimes

def getNearestBusStop(bus, direction, userLocation):
    allLocations = dbMoves.getAllLocations()
    currentBusStops = bus.stops.directions[direction]
    busStopLocations = [ltn for ltn in allLocations if ltn.name in currentBusStops]
    minDist, nearestBusStop = float('inf'), busStopLocations[0].name
    for ltn in busStopLocations:
        dist = getDistanceByHaversine(userLocation, ltn)
        if dist < minDist:
            minDist = dist
            nearestBusStop = ltn.name
    return nearestBusStop

async def incorrectBusNameHandler(message):
    userInfo = getUserInfo(message=message)
    dbLocal.setCurrentBus(userInfo.userId, None)
    botMessage = await message.answer(getTranslation(userInfo, 'incorrect.busname.message'))
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)

def isBusListCommand(userInfo):
    return userInfo.userText.lower() == getTranslation(userInfo, 'button.buses').lower()

def getBusListKeyboard():
    busNamesButtons = [[types.InlineKeyboardButton(text=name, callback_data=f'{const.callback.prefix.bus}_{name}')]
                       for name in const.data.availableBuses]
    inlineKeyboard = types.InlineKeyboardMarkup(inline_keyboard=busNamesButtons)
    return inlineKeyboard

async def busListHandler(message):
    userInfo = getUserInfo(message=message)
    await removeLastMessageIds(userInfo)
    busListKeyboard = getBusListKeyboard()
    botMessage = await message.answer(getTranslation(userInfo, 'buslist.message'), reply_markup=busListKeyboard)
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)

def isFavouritesCommand(userInfo):
    return userInfo.userText.lower() == getTranslation(userInfo, 'button.favourites').lower()

def getFavouritesKeyboard(busNameList):
    busNamesButtons = [[types.InlineKeyboardButton(text=name, callback_data=f'{const.callback.prefix.bus}_{name}')]
                       for name in busNameList]
    inlineKeyboard = types.InlineKeyboardMarkup(inline_keyboard=busNamesButtons)
    return inlineKeyboard

async def favouritesHandler(message):
    userInfo = getUserInfo(message=message)
    await removeLastMessageIds(userInfo)
    user = dbUsers.getUser(userInfo.userId)
    if user.favourites:
        favouritesKeyboard = getFavouritesKeyboard(user.favourites)
        botMessage = await message.answer(getTranslation(userInfo, 'buslist.favourites.message'), reply_markup=favouritesKeyboard)
    else:
        botMessage = await message.answer(getTranslation(userInfo, 'buslist.favourites.message.empty'))
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)

def isUnknownCommand(userInfo):
    return userInfo.userText and userInfo.userText[0] == '/'

async def unknownCommandHandler(message):
    userInfo = getUserInfo(message=message)
    await removeLastMessageIds(userInfo)
    mainKeyboard = getMainKeyboard(userInfo)
    botMessage = await message.answer(getTranslation(userInfo, 'unknown.command.message'), reply_markup=mainKeyboard)
    dbUsers.addRemovedMessageIds(userInfo.userId, botMessage.message_id)

@dp.message()
async def mainHandler(message: types.Message):
    userInfo = getUserInfo(message=message)

    if isAboutCommand(userInfo):
        await startHandler(message)
        return
    elif isBusListCommand(userInfo):
        await busListHandler(message)
        return
    elif isFavouritesCommand(userInfo):
        await favouritesHandler(message)
        return
    elif isUnknownCommand(userInfo):
        await unknownCommandHandler(message)
        return

    correctBusName = getCorrectBusName(userInfo.userText)
    if correctBusName is None:
        await incorrectBusNameHandler(message)
    else:
        await chooseDirectionBusHandler(userInfo, correctBusName)


async def mainTelegram():
    await dp.start_polling(bot)

def main():
    asyncio.run(mainTelegram())

if __name__ == '__main__':
    main()