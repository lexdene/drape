''' module for cookie '''
import time

GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


class Cookie(object):
    ''' cookie object '''
    def __init__(self, request):
        self.__request = request

        # data read from request
        self.__requestdata = dict()

        # data to flush to response
        self.__response_data = list()

        self._run()

    def _run(self):
        ''' read cookie data from request '''
        cookiestr = self.__request.HTTP_COOKIE
        if not cookiestr is None:
            part_list = cookiestr.split(';')
            for part in part_list:
                part_splits = part.split('=', 2)
                if len(part_splits) < 2:
                    continue
                key = part_splits[0].strip()
                value = part_splits[1].strip()

                self.__requestdata[key] = value

    def get(self, key, value=None):
        ''' get cookie data '''
        return self.__requestdata.get(key, value)

    def iteritems(self):
        ''' iter cookie data '''
        return iter(self.__requestdata.items())

    def add(self, key, value, path='/', expires=None, domain=None):
        ''' add cookie data '''
        # path can be string or tuple
        if isinstance(path, tuple):
            path, path_type = path
        else:
            path_type = 'relative'

        # expires can be float or tuple
        if isinstance(expires, tuple):
            expires, expires_type = expires
        else:
            expires_type = 'relative'

        if 'relative' == path_type:
            path = self.__request.root_path() + path

        if not expires is None:
            if 'relative' == expires_type:
                expires = float(expires) + time.time()
            else:
                expires = float(expires)

        self.__add_data(dict(
            key=key,
            value=value,
            path=path,
            expires=expires,
            domain=domain
        ))

    def flush(self, response_obj):
        ''' flush data to response '''
        for data in self.__response_data:
            response_obj.add_header(
                'Set-Cookie',
                data
            )

    def __add_data(self, cookiedata):
        ''' add data in response data '''
        cookie_str = '%(key)s=%(value)s; Path=%(path)s' % cookiedata

        if not cookiedata['expires'] is None:
            time_struct = time.gmtime(cookiedata['expires'])
            cookiedata['expires'] = time.strftime(GMT_FORMAT, time_struct)
            cookie_str += '; Expires=%(expires)s' % cookiedata

        if not cookiedata['domain'] is None:
            cookie_str += '; Domain=%(domain)s' % cookiedata

        self.__response_data.append(cookie_str)
