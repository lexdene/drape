# -*- coding: utf-8 -*-
''' default config for drape '''


SYSTEM_IS_DEBUG = True
NOTFOUND_PAGE = 'notfound/Index'
DEFAULT_MOD = 'index'
DEFAULT_CONTROLLER = 'Index'

DB_DRIVER = 'mysql'
DB_NAME = ''
DB_USER = ''
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_PORT = 3306
DB_CHARSET = 'utf8'
DB_TABLE_PREFIX = ''
DB_LOG_SQL = True

DEFAULT_TEMPLATOR = 'jinja2'

SESSION_STORE_ENGINE = 'file'
SESSION_FILE_DIRECTORY = 'data/session'
SESSION_COOKIE_NAME = 'drape_session_id'
SESSION_TIMEOUT = 10 * 24 * 3600
SESSION_SECRET_KEY = 'drape_web_framework'

TEMPLATE_DIR = 'template'


class ConfigWrapper:
    def __init__(self):
        self.__modules = []

    def register(self, module):
        self.__modules.append(module)

    def __getattr__(self, key):
        for module in self.__modules:
            value = getattr(module, key, None)
            if value is not None:
                return value

        return getattr(self.__class__.__module__, key)


config = ConfigWrapper()
