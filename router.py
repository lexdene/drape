''' routes '''
import re

from .util import pluralize
from .request import GET, POST, DELETE, PUT


class RouterBase(object):
    def __init__(self):
        import app.controller
        self._model = app.controller

    def match(self, path, method):
        return None

    def _controller(self, controller_name, action_name, params):
        if controller_name:
            module = getattr(self._model, controller_name, None)
        else:
            module = self._model
        if module is None:
            return None

        action = getattr(module, action_name, None)
        if action is None:
            return None

        def resource_controller(request):
            return action(request, **params)

        return resource_controller


KEY_REGEXP_MAP = {
    'number': '[0-9]',
    'word': '[a-z]'
}


class Resource(RouterBase):
    def __init__(self, name, key=None, key_type='number'):
        self.__name = name

        if key is None:
            key = '%s_id' % self.__name
        self.__param = {
            'key': key,
            'key_type': key_type
        }
        self.__routes = list(self.__generate_routes())

    def match(self, path, method):
        for path_reg, action_map in self.__routes:
            match = path_reg.match(path)

            if match and method in action_map:
                return self._controller(
                    self.__name,
                    action_map[method],
                    match.groupdict()
                )

    def __generate_routes(self):
        plural = pluralize(self.__name)

        plural_path = r'^/%s$' % plural

        yield (
            re.compile(plural_path),
            {
                GET: 'index',
                POST: 'create',
            }
        )

        singular_path = r'^/%s/(?P<%s>%s+)$' % (
            self.__name,
            self.__param['key'],
            KEY_REGEXP_MAP[self.__param['key_type']]
        )

        yield (
            re.compile(singular_path),
            {
                GET: 'one',
                PUT: 'update',
                DELETE: 'delete'
            }
        )


class Group(RouterBase):
    def __init__(self, name, *children):
        super(Group, self).__init__()
        self.__name = name
        self.__children = children

        for child in self.__children:
            child._model = getattr(self._model, self.__name, None)

        self.__path_reg = re.compile(r'^/%s/(?P<sub>.*)$' % self.__name)

    def match(self, path, method):
        result = self.__path_reg.match(path)

        if result:
            subpath = '/' + result.group('sub')
            for child in self.__children:
                ctrl = child.match(
                    subpath,
                    method
                )
                if ctrl:
                    return ctrl


class Url(RouterBase):
    def __init__(self, url, method, name):
        super(Url, self).__init__()

        self.__url_reg = re.compile(url)
        self.__method = method
        self.__name = name

    def match(self, path, method):
        if method == self.__method:
            result = self.__url_reg.match(path)
            if result:
                return self._controller(
                    None,
                    self.__name,
                    result.groupdict()
                )
