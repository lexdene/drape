# -*- coding: utf-8 -*-
''' 控制器相关模块 '''
from functools import wraps

from . import config, render, response


class Controller(object):
    ''' 控制器的基类 '''
    def __init__(self, runbox):
        self.__runbox = runbox

        # path
        mod = self.__module__.split('.')[-1]
        cls = self.__class__.__name__
        self.__path = '/%s/%s' % (mod, cls)

        # vars are for view render
        self.__vars = dict()

        self.__template_path = None
        self.__render_func = None

        self.__parent = None

    def set_variable(self, name, value):
        ''' 设置模板变量 '''
        self.__vars[name] = value

    def path(self):
        ''' 获取当前控制器的path '''
        return self.__path

    def _set_template_path(self, template_path):
        ''' 设置模板文件路径 '''
        self.__template_path = template_path

    def __get_template_path(self):
        '''
            获取模板文件路径
            如果未设置过，默认与path相同
        '''
        if self.__template_path:
            return self.__template_path
        else:
            return self.__path

    def _set_parent(self, parent):
        ''' 设置父控制器 '''
        if isinstance(parent, str):
            parent = self.__runbox.controller(parent)
        self.__parent = parent

    def run(self):
        ''' 执行控制器 '''
        self.process()

        render_result = self.render(
            self.__get_template_path(),
            self.__vars
        )
        if not self.__parent is None:
            self.__parent.set_variable('body', render_result)
            return self.__parent.run()
        else:
            return render_result

    def process(self):
        ''' 处理请求 '''
        pass

    def render(self, template_path, variables):
        ''' 渲染模板 '''
        if self.__render_func is None:
            template = config.get_value('view/default_templator')
            render_func_map = {
                'jinja2': render.jinja2,
                'mako': render.mako
            }
            self.__render_func = render_func_map[template]

        return self.__render_func(
            template_path,
            variables
        )

    def runbox(self):
        ''' 执行包 '''
        return self.__runbox

    def request(self):
        ''' 请求对象 '''
        return self.__runbox.request()

    def response(self):
        ''' 响应对象 '''
        return self.__runbox.response()

    def session(self):
        ''' 会话对象 '''
        return self.__runbox.session()

    def params(self):
        ''' 请求参数 '''
        return self.request().params()

    @classmethod
    def controller(cls, fun):
        ''' 将一个process函数转成一个控制器类 '''
        return type(
            fun.__name__,
            (cls, ),
            {
                'process': fun,
                '__module__': fun.__module__
            }
        )


class JsonController(Controller):
    ''' 返回json的控制器 '''
    def __init__(self, runbox):
        super(JsonController, self).__init__(runbox)

        response_obj = self.response()
        response_obj.set_header(
            'Content-Type',
            'application/json; charset=utf-8'
        )

    def render(self, template_path, variables):
        return render.json(
            template_path,
            variables
        )


class HTTPError(Exception):
    ''' 所有http错误的基类 '''
    def __init__(self, http_code):
        self.__code = http_code
        self.__desc = response.get_desc_by_code(http_code)

    @property
    def code(self):
        return self.__code

    @property
    def description(self):
        return self.__desc


class NotAllowed(HTTPError):
    ''' 405 Method Not Allowed '''
    def __init__(self):
        super(NotAllowed, self).__init__(405)


class Forbidden(HTTPError):
    ''' 403 Forbidden '''
    def __init__(self):
        super(Forbidden, self).__init__(403)


def post_only(func):
    ''' 只接受POST请求 '''
    @wraps(func)
    def new_func(self):
        ''' 检查 request method 是不是post '''
        method = self.runbox().request().REQUEST_METHOD
        if method == 'POST':
            func(self)
        else:
            raise NotAllowed
    return new_func
