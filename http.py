# -*- coding: utf-8 -*-
''' http functions '''
from functools import wraps

from . import response, router, config


class HTTPError(Exception):
    ''' 所有http错误的基类 '''
    def __init__(self, http_code):
        super(HTTPError, self).__init__()

        self.__code = http_code
        self.__desc = response.get_desc_by_code(http_code)

    @property
    def code(self):
        ''' error code '''
        return self.__code

    @property
    def description(self):
        ''' error description '''
        return self.__desc

    def body(self):
        ''' error body '''
        return self.description


class BadRequest(HTTPError):
    ''' 400 Bad Request '''
    def __init__(self, msg):
        super(BadRequest, self).__init__(400)

        self.__msg = msg

    def body(self):
        return self.__msg


class Unauthorized(HTTPError):
    ''' 401 Unauthorized '''
    def __init__(self):
        super(Unauthorized, self).__init__(401)


class NotFound(HTTPError):
    ''' 404 Not Found '''
    def __init__(self, path):
        super(NotFound, self).__init__(404)

        self.__path = path

    def body(self):
        if config.config.SYSTEM_IS_DEBUG:
            return 'can not found: %s\n%s' % (
                self.__path,
                '\n'.join(
                    ('%7s: %s' % (r[1], r[0]) for r in router.routes())
                )
            )
        else:
            return 'can not found: %s' % self.__path


class NotAllowed(HTTPError):
    ''' 405 Method Not Allowed '''
    def __init__(self):
        super(NotAllowed, self).__init__(405)


class Forbidden(HTTPError):
    ''' 403 Forbidden '''
    def __init__(self):
        super(Forbidden, self).__init__(403)
