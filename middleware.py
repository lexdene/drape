''' middlewares '''
import traceback

import config
import response
import http
import cookie
import session
from import_util import import_obj, import_module


def run(request):
    ''' run all middlewares '''
    middlewares = list(config.MIDDLEWARES)

    return recursion_run(request, middlewares)


def recursion_run(request, middlewares):
    ''' run one middleware and recursion others '''
    if not middlewares:
        return None
    first_middleware_class_name = middlewares.pop()
    first_middleware_class = import_obj(first_middleware_class_name)
    first_middleware = first_middleware_class()

    try:
        response_obj = first_middleware.process_request(request)
        if response_obj:
            return response_obj

        response_obj = recursion_run(request, middlewares)
        first_middleware.process_response(response_obj)
        return response_obj
    except Exception as err:
        response_obj = first_middleware.process_exception(err)
        if response_obj:
            return response_obj
        else:
            raise


class Base(object):
    ''' base for middleware class '''
    def __init__(self):
        self._request = None
        self._response = None

    def process_request(self, request):
        '''
            process request before run
            stop other middlewares by returning a response object
        '''
        self._request = request

    def process_response(self, response_obj):
        '''
            process response after inner return
        '''
        pass

    def process_exception(self, exception):
        '''
            process exception throw by inner run
        '''
        pass


class ExceptionTraceback(Base):
    ''' catch all exception and print them '''
    def process_exception(self, exception):
        body = ''
        if config.SYSTEM_IS_DEBUG:
            body += 'controller path: %s\n' % self._request.controller_path()
            body += traceback.format_exc()

            body += 'environ:\n'
            for key, value in self._request.env.iteritems():
                body += '%s => %s\n' % (key, value)

        else:
            body = response.ERROR

        return response.Response(
            status=response.ERROR,
            headers={
                'Content_Type': 'text/plain; charset=utf-8'
            },
            body=body
        )


class HttpErrorProcessor(Base):
    ''' catch all http error and make http response '''
    def process_exception(self, exception):
        if isinstance(exception, http.HTTPError):
            return response.Response(
                status=exception.description,
                headers={
                    'Content-Type': 'text/plain; charset=utf-8'
                },
                body=exception.body()
            )


class CookieWrapper(Base):
    ''' start cookie '''
    def process_request(self, request):
        super(CookieWrapper, self).process_request(request)

        request.cookie = cookie.Cookie(request)

    def process_response(self, response_obj):
        self._request.cookie.flush(response_obj)


class SessionWrapper(Base):
    ''' start session '''
    def process_request(self, request):
        super(SessionWrapper, self).process_request(request)

        request.session = session.Session(request)

    def process_response(self, response_obj):
        self._request.session.save()


class ExtraHeaders(Base):
    ''' add extra headers '''
    def process_response(self, response_obj):
        if not response_obj.has_header('Content-Type'):
            response_obj.set_header(
                'Content-Type',
                'text/html; charset=utf-8'
            )

        response_obj.set_header(
            'X-Powered-By',
            'python-drape'
        )


class ControllerRunner(Base):
    ''' find controller by path and run '''
    def process_request(self, request):
        super(ControllerRunner, self).process_request(request)

        path = request.controller_path()
        module_name, controller_name = path.split('/')

        if not module_name:
            module_name = config.DEFAULT_MOD

        try:
            module = import_module('app.controller.%s' % module_name)
        except ImportError as err:
            if err.args[0] == 'No module named %s' % module_name:
                raise http.NotFound(path)
            else:
                raise

        if not controller_name:
            controller_name = getattr(
                module,
                'DEFAULT_CONTROLLER',
                config.DEFAULT_CONTROLLER
            )

        controller = getattr(
            module,
            controller_name,
            None
        )

        if not controller:
            raise http.NotFound(path)

        response_obj = controller(request)
        if isinstance(response_obj, response.Response):
            return response_obj
        else:
            raise ValueError('not a response object: %s' % response_obj)
