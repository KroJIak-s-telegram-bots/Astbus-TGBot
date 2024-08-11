
from utils.funcs import joinPath

class configCategoryObject:
    def __init__(self, config, nameCategory):
        self.config = config
        self.nameCategory = nameCategory

    def get(self, elm):
        return self.config.get(self.nameCategory, elm)

class Telegram(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Telegram')
        self.token = self.get('token')
        self.alias = self.get('alias')

class Data(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Data')
        self.defaultLang = self.get('defaultLang')
        self.availableBuses = sorted(self.get('availableBuses').split(';'))
        self.timezone = self.get('timezone')

class Logging:
    def __init__(self):
        self.format = '%(asctime)s %(levelname)s %(message)s'

class Path:
    def __init__(self):
        self.project = joinPath('/', *__file__.split('/')[:-2])
        self.cache = joinPath(self.project, 'cache')
        self.userData = joinPath(self.cache, 'web/user')
        self.client = joinPath(self.project, 'client')
        self.config = joinPath(self.client, 'config')
        self.lang = joinPath(self.client, 'lang')
        self.logs = joinPath(self.client, 'logs')
        self.db = joinPath(self.project, 'db')
        self.moves = joinPath(self.db, 'moves')
        self.users = joinPath(self.db, 'users')
        self.utils = joinPath(self.project, 'utils')
        self.objects = joinPath(self.utils, 'objects')
        self.parser = joinPath(self.utils, 'parser')

class File:
    def __init__(self):
        self.config = 'bot.ini'
        self.database = 'database.json'

class Default:
    def __init__(self):
        self.parseMode = 'HTML'

class Prefix:
    def __init__(self):
        self.bus = 'bus'
        self.direction = 'direction'
        self.busstop = 'busstop'

class Callback:
    def __init__(self):
        self.removefavourites = 'removefavourites'
        self.addfavourites = 'addfavourites'
        self.location = 'location'
        self.busstop = 'busstop'
        self.prefix = Prefix()

class ConstPlenty:
    def __init__(self, config=None):
        if config: self.addConstFromConfig(config)
        self.path = Path()
        self.default = Default()
        self.logging = Logging()
        self.file = File()
        self.callback = Callback()

    def addConstFromConfig(self, config):
        self.telegram = Telegram(config)
        self.data = Data(config)