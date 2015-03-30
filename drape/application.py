''' application '''


instance = None


class Base(object):
    ''' base application '''
    def __init__(self):
        self.app_init()

        global instance
        instance = self

    def app_init(self):
        ''' run for one time '''
        pass

    def run(self, _env):
        ''' run for each request '''
        pass


class WsgiApplication(Base):
    ''' application for wsgi '''
    def run(self, env):
        from . import request, middleware

        request_obj = request.Request(env, self)

        return middleware.run(request_obj)

    def __call__(self, env, start_response):
        # response
        response_obj = self.run(env)

        # header
        start_response(
            response_obj.status(),
            list(response_obj.headers())
        )

        # body
        body = response_obj.body()
        if isinstance(body, str):
            yield body.encode('utf-8')
        else:
            yield body
