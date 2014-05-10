# -*- coding: utf-8 -*-
''' 响应相关模块 '''

from .render import json

# response codes
OK = '200 OK'
REDIRECT = '301 Moved Permanently'
BAD_REQUEST = '400 Bad request'
FORBIDDEN = '403 Forbidden'
NOT_FOUND = '404 Not Found'
NOT_ALLOWED = '405 Method Not Allowed'
ERROR = '500 Internal Server Error'

# response headers
CONTENT_TYPE = 'Content-Type'


def get_desc_by_code(status_code):
    ''' 通过http状态码获取描述信息 '''
    desc_map = {
        200: OK,
        301: REDIRECT,
        400: BAD_REQUEST,
        403: FORBIDDEN,
        404: NOT_FOUND,
        405: NOT_ALLOWED,
        500: ERROR,
    }
    return desc_map[status_code]


class Response(object):
    ''' 响应对象 '''
    def __init__(self, status=OK, headers=None, body=''):
        self.__status = status

        self.__headers = dict()
        if headers:
            for key, value in headers.items():
                self.__headers[key] = str(value)

        self.__body = body

    def set_status(self, status):
        ''' 设置响应状态 '''
        self.__status = status

    def set_header(self, key, value):
        ''' 设置响应头部，相同名称的头部只能有一个值 '''
        self.__headers[key] = value

    def add_header(self, key, value):
        ''' 添加响应头部，相同名称的头部可以有多少值 '''
        if key in self.__headers:
            if not isinstance(self.__headers[key], list):
                self.__headers[key] = [self.__headers[key]]
        else:
            self.__headers[key] = list()

        self.__headers[key].append(value)

    def set_body(self, body):
        ''' 设置响应主体 '''
        self.__body = body

    def status(self):
        ''' 响应状态 '''
        return self.__status

    def headers(self):
        ''' 遍历所有的头部信息 '''
        for key, value in self.__headers.items():
            if isinstance(value, list):
                for value_item in value:
                    yield key, str(value_item)
            else:
                yield key, str(value)

    def body(self):
        ''' 响应主体 '''
        return self.__body

    def has_header(self, name):
        ''' 判断是否包含某个header '''
        return name in self.__headers


def json_response(obj, headers=None, status=OK):
    if headers is None:
        headers = {}
    headers[CONTENT_TYPE] = 'application/json; charset=utf-8'
    return Response(
        status=status,
        headers=headers,
        body=json(obj)
    )


def plaintext_response(obj):
    return Response(
        headers={
            CONTENT_TYPE: 'text/plain; charset=utf-8',
        },
        body=str(obj)
    )
