''' routes '''
import re
import itertools
import operator

from .util import pluralize
from .request import GET, POST, DELETE, PUT


class RouterBase(object):
    def __init__(self):
        pass

    def routes(self):
        raise NotImplementedError


KEY_REGEXP_MAP = {
    'number': '[0-9]',
    'word': '[a-z]'
}


class Resource(RouterBase):
    def __init__(self, name, key=None, key_type='number', members=None):
        super(Resource, self).__init__()

        self.__name = name

        if key is None:
            self.__key = '%s_id' % self.__name
        else:
            self.__key = key

        self.__key_type = key_type

        if members:
            self.__members = members
        else:
            self.__members = []

    def routes(self):
        plural_path = pluralize(self.__name)

        yield (plural_path, GET, self.__name + '.index')
        yield (plural_path, POST, self.__name + '.create')

        singular_path = r'%s/(?P<%s>%s+)' % (
            self.__name,
            self.__key,
            KEY_REGEXP_MAP[self.__key_type]
        )

        yield (singular_path, GET, self.__name + '.show')
        yield (singular_path, PUT, self.__name + '.update')
        yield (singular_path, DELETE, self.__name + '.delete')

        for member in self.__members:
            for route in member.routes():
                yield (
                    singular_path + '/' + route[0],
                    route[1],
                    route[2]
                )


class Group(RouterBase):
    def __init__(self, name, *children):
        super(Group, self).__init__()
        self.__name = name
        self.__children = children

    def routes(self):
        for child in self.__children:
            for route in child.routes():
                yield (
                    self.__name + '/' + route[0],
                    route[1],
                    self.__name + '.' + route[2]
                )


class Url(RouterBase):
    def __init__(self, url, method, name):
        super(Url, self).__init__()

        self.__url = url
        self.__method = method
        self.__name = name

    def routes(self):
        yield (
            self.__url,
            self.__method,
            self.__name
        )

    @classmethod
    def create(cls, method, url, name=None):
        if name is None:
            name = url.replace('/', '.')
        return cls(url, method, name)

    @classmethod
    def get(cls, url, name=None):
        return cls.create(GET, url, name)

    @classmethod
    def post(cls, url, name=None):
        return cls.create(POST, url, name)


_ROUTES = []
_COMPILED_ROUTES = None


def define_routes(*argv):
    global _ROUTES

    for arg in argv:
        for route in arg.routes():
            _ROUTES.append(route)


def compile_routes():
    global _COMPILED_ROUTES

    if _COMPILED_ROUTES is None:
        _COMPILED_ROUTES = [
            (
                re.compile('^/' + k + '$'),
                dict(v[1:] for v in vv)
            )
            for k, vv in itertools.groupby(_ROUTES, operator.itemgetter(0))
        ]


def find_controller(module, path, method):
    for route in _COMPILED_ROUTES:
        match = route[0].match(path)
        if match and method in route[1]:
            controller_path = route[1][method]

            return _controller(
                module,
                controller_path,
                match.groupdict()
            )


def _controller(controller, controller_path, params):
    for name_part in controller_path.split('.'):
        controller = getattr(controller, name_part)

    def resource_controller(request):
        for key, value in params.items():
            request.set_param(key, value)

        return controller(request)

    return resource_controller
