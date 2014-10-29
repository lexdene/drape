''' module for session '''
import time
import re
import base64
import pickle
import os

from . import config
from . import util


class StoreBase(object):
    ''' Base for store engine '''
    @classmethod
    def create(cls, store_engine, app):
        ''' create a store obj '''
        store_class_map = {
            'file': FileStore,
        }
        store_cls = store_class_map.get(store_engine)

        if store_cls is None:
            raise ValueError('no such store type:%s' % store_engine)

        store = store_cls(app)

        # cleanup
        store.cleanup()

        return store

    def __init__(self, app):
        self._app = app

    def get(self, key, value=None):
        ''' get value from store '''
        if key in self:
            return self[key]
        else:
            return value

    def cleanup(self):
        ''' clean up old data '''
        raise NotImplementedError

    def __contains__(self, key):
        raise NotImplementedError

    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError


BUF_SIZE = 1024 * 24


class FileStore(StoreBase):
    ''' store by file '''
    def _directory(self):
        return os.path.join(
            self._app.root_dir,
            config.config.SESSION_FILE_DIRECTORY
        )

    def __contains__(self, key):
        directory = self._directory()
        path = '%s/%s' % (directory, key)
        return os.path.isfile(path)

    def __getitem__(self, key):
        directory = self._directory()
        path = '%s/%s' % (directory, key)
        if not os.path.isfile(path):
            return None

        with open(path, 'rb') as fin:
            content = fin.read(BUF_SIZE)

        return content

    def __setitem__(self, key, value):
        directory = self._directory()
        util.mkdir_not_existing(directory)

        path = '%s/%s' % (directory, key)

        with open(path, 'wb') as fout:
            fout.write(value)

    def cleanup(self):
        directory = self._directory()
        timeout = config.config.SESSION_TIMEOUT
        now = time.time()

        if not os.path.isdir(directory):
            return
        for path in os.listdir(directory):
            path = os.path.join(directory, path)
            atime = os.stat(path).st_atime
            if now - atime > timeout:
                os.remove(path)


_SESSION_ID_REG = re.compile('^[0-9a-fA-F]+$')


def _valid_session_id(session_id):
    ''' valid session id '''
    return _SESSION_ID_REG.match(session_id)


def _recreate_session_id(ip_address, secret_key, store):
    ''' recreate session id '''
    while True:
        rand = os.urandom(16)
        now = time.time()
        session_id = util.sha1sum(
            "%s%s%s%s" % (rand, now, ip_address, secret_key)
        )

        if session_id not in store:
            break
    return session_id


def _init_session_data(remote_address, timeout):
    ''' init data in session '''
    return {
        '_remote_address': remote_address,
        '_expired': time.time() + timeout
    }


def _decode_data(rawdata):
    ''' decode data '''
    pickled = base64.decodestring(rawdata)
    return pickle.loads(pickled)


def _encode_data(data):
    ''' encode data '''
    pickled = pickle.dumps(data)
    return base64.encodestring(pickled)


class Session(object):
    ''' session obj '''
    def __init__(self, request):
        self.__request = request
        self.__store = None
        self.__session_id = None
        self.__data = dict()

        self._run()

    def _run(self):
        ''' read data from store '''
        cookie_name = config.config.SESSION_COOKIE_NAME
        request = self.__request
        cookie = request.cookie
        self.__store = StoreBase.create(
            config.config.SESSION_STORE_ENGINE,
            self.__request.app
        )

        # read session id from cookie
        self.__session_id = cookie.get(cookie_name)

        # protection against session_id tampering
        if self.__session_id and not _valid_session_id(self.__session_id):
            self.__session_id = None

        # need recreate data ?
        if self.__session_id:
            rawdata = self.__store.get(self.__session_id)
            if rawdata is None:
                self.__data = _init_session_data(
                    request.REMOTE_ADDR,
                    config.config.SESSION_TIMEOUT
                )
            else:
                self.__data = _decode_data(rawdata)

            # validate address
            # check expired time
            if request.REMOTE_ADDR != self.get('_remote_address') \
                    or time.time() > self.get('_expired'):
                self.__data = _init_session_data(
                    request.REMOTE_ADDR,
                    config.config.SESSION_TIMEOUT
                )

        # recreate session_id
        if self.__session_id is None:
            self.__session_id = _recreate_session_id(
                request.REMOTE_ADDR,
                config.config.SESSION_SECRET_KEY,
                self.__store
            )
            cookie.add(cookie_name, self.__session_id)
            self.__data = _init_session_data(
                request.REMOTE_ADDR,
                config.config.SESSION_TIMEOUT
            )

    def set_cookie_attr(self, path='/', expired=None, domain=None):
        ''' set attr of the cookie for session '''
        cookie_name = config.config.SESSION_COOKIE_NAME
        cookie = self.__request.cookie
        cookie.add(cookie_name, self.__session_id, path, expired, domain)

    def save(self):
        ''' save the data to store '''
        rawdata = _encode_data(self.__data)
        self.__store[self.__session_id] = rawdata

    def iteritems(self):
        ''' iter the data '''
        for key, value in self.__data.items():
            if key[0] != '_':
                yield (key, value)

    def get(self, key, value=None):
        ''' get a value by key '''
        return self.__data.get(key, value)

    def set(self, key, value):
        ''' set a value '''
        if key is None:
            raise KeyError('key can not be None')
        elif value is None:
            if key in self.__data:
                del self.__data[key]
        else:
            self.__data[key] = value

    def remove(self, key):
        ''' remove a value in session '''
        if key in self.__data:
            del self.__data[key]
