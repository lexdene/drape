# -*- coding: utf-8 -*-
''' 封装请求数据 '''

import cgi

GET = 'GET'
POST = 'POST'
DELETE = 'DELETE'
PUT = 'PUT'


class Request(object):
    ''' request object '''
    def __init__(self, env):
        self.env = env

        self.__path = ''  # only path
        self.__url = ''  # path and query string

        self.__field_storage = None
        self.__params = dict()

        self.__run()

    def __run(self):
        ''' process params in env '''
        # path
        self.__path = self.env.get('PATH_INFO')

        # url path
        self.__url = self.__path
        query = self.env.get('QUERY_STRING')
        if query is not None and len(query) > 0:
            self.__url += '?' + query

        # field storage
        self.__field_storage = cgi.FieldStorage(
            fp=self.env['wsgi.input'],
            environ=self.env,
            keep_blank_values=True
        )
        for key in self.__field_storage:
            value = self.__field_storage[key]
            if key[-2:] == '[]':
                real_key = key[:-2]
                if isinstance(value, list):
                    self.__params[real_key] = [
                        v.value if v.filename is None else v
                        for v in value
                    ]
                else:
                    self.__params[real_key] = [
                        value.value if value.filename is None else value
                    ]
            else:
                if isinstance(value, list):
                    value = value[-1]
                # file or string
                if value.filename is None:
                    self.__params[key] = value.value
                else:
                    self.__params[key] = value

    def __getattr__(self, key):
        return self.env.get(key, None)

    def method(self):
        return self.REQUEST_METHOD

    def root_path(self):
        ''' WEB ROOT '''
        return self.SCRIPT_NAME

    def path(self):
        ''' only path '''
        return self.__path

    def url(self):
        ''' path and query string '''
        return self.__url

    def params(self):
        ''' request params '''
        return self.__params

    def set_param(self, key, value):
        self.__params[key] = value
