''' application '''

import request
import middleware

class Base(object):
    ''' base application '''
    def __init__(self):
        self.app_init()

    def app_init(self):
        ''' run for one time '''
        pass

    def run(self, _env):
        ''' run for each request '''
        pass

class WsgiApplication(Base):
    ''' application for wsgi '''
    def run(self, env):
        request_obj = request.Request(env)

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
        if isinstance(body, unicode):
            return body.encode('utf-8')
        else:
            return body
