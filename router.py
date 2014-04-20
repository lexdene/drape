''' routes '''
import re

from .util import pluralize
from .request import GET, POST, DELETE, PUT

class RouterBase(object):
    def match(self, path, method):
        return None


class Resource(RouterBase):
    def __init__(self, name):
        self.__name = name

        self.__routes = list(self.__generate_routes())

    def match(self, path, method):
        for path_reg, action_map in self.__routes:
            match = path_reg.match(path)

            if match and method in action_map:
                return self.controller(
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

        singular_path = r'^/%s/(?P<%s_id>[0-9]+)$' % (
            self.__name,
            self.__name
        )

        yield (
            re.compile(singular_path),
            {
                GET: 'one',
                PUT: 'update',
                DELETE: 'delete'
            }
        )

    @classmethod
    def controller(cls, controller_name, action_name, params):
        import app.controller

        module = getattr(app.controller, controller_name, None)
        if module is None:
            return None

        action = getattr(module, action_name, None)
        if action is None:
            return None

        def resource_controller(request):
            return action(request, **params)

        return resource_controller
