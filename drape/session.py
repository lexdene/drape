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
    def create(cls, store_engine):
        ''' create a store obj '''
        store_cls = STORE_CLASS_MAP.get(store_engine)

        if store_cls is None:
            raise ValueError('no such store type:%s' % store_engine)

        store = store_cls()

        return store

    def get(self, key, value=None):
        ''' get value from store '''
        if key in self:
            return self[key]
        else:
            return value

    def __contains__(self, key):
        raise NotImplementedError

    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError


BUF_SIZE = 1024 * 24


class FileStore(StoreBase):
    ''' store by file '''
    def __init__(self):
        self._cleanup()

    def _directory(self):
        config.SESSION_FILE_DIRECTORY

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

        return _decode_data(content)

    def __setitem__(self, key, value):
        directory = self._directory()
        util.mkdir_not_existing(directory)

        path = '%s/%s' % (directory, key)

        with open(path, 'wb') as fout:
            fout.write(_encode_data(value))

    def _cleanup(self):
        directory = self._directory()
        timeout = config.SESSION_TIMEOUT
        now = time.time()

        if not os.path.isdir(directory):
            return
        for path in os.listdir(directory):
            path = os.path.join(directory, path)
            atime = os.stat(path).st_atime
            if now - atime > timeout:
                os.remove(path)


class MemStore(StoreBase):
    'store by memcache'
    def __init__(self):
        super(MemStore, self).__init__()

        import memcache
        self.__connection = memcache.Client(
            config.SESSION_MEMCACHE_CONNECTIONS
        )

    def _key(self, key):
        return 'session/%s' % key

    def __contains__(self, key):
        value = self[key]
        if value:
            return True
        else:
            return False

    def __getitem__(self, key):
        key = self._key(key)
        value = self.__connection.get(key)
        return value

    def __setitem__(self, key, value):
        key = self._key(key)
        self.__connection.set(key, value, config.SESSION_TIMEOUT)


STORE_CLASS_MAP = {
    'file': FileStore,
    'memcache': MemStore,
}


_SESSION_ID_REG = re.compile('^[0-9a-fA-F]+$')


def _valid_session_id(session_id):
    ''' valid session id '''
    return _SESSION_ID_REG.match(session_id)


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
        self.__cookie_data = None

        self._run()

    def _create_session_id(self):
        ''' recreate session id '''
        secret_key, store = config.SESSION_SECRET_KEY, self.__store

        while True:
            rand = os.urandom(16)
            now = time.time()
            session_id = util.sha1sum(
                "%s.%s.%s" % (rand, now, secret_key)
            )

            if session_id not in store:
                break
        return session_id

    def _run(self):
        ''' read data from store '''
        cookie_name = config.SESSION_COOKIE_NAME
        cookie = self.__request.cookie
        self.__store = StoreBase.create(
            config.SESSION_STORE_ENGINE
        )

        # read session id from cookie
        self.__session_id = cookie.get(cookie_name)

        # protection against session_id tampering
        if self.__session_id and not _valid_session_id(self.__session_id):
            self.__session_id = None

        # recreate session_id
        if self.__session_id is None:
            self.__session_id = self._create_session_id()
            self.set_cookie_attr()

            self.__data = {}
        else:
            self.__data = self.__store.get(self.__session_id, {})

    def set_cookie_attr(self, path='/', expired=None, domain=None):
        ''' set attr of the cookie for session '''
        cookie_name = config.SESSION_COOKIE_NAME
        self.__cookie_data = (
            cookie_name, self.__session_id, path, expired, domain
        )

    def save(self):
        ''' save the data to store '''
        self.__store[self.__session_id] = self.__data

        if self.__cookie_data:
            self.__request.cookie.add(*self.__cookie_data)

    def items(self):
        ''' iter the data '''
        return self.__data.items()

    def get(self, key, value=None):
        ''' get a value by key '''
        return self.__data.get(key, value)

    def set(self, key, value):
        ''' set a value '''
        self.__data[key] = value

    def remove(self, key):
        ''' remove a value in session '''
        if key in self.__data:
            del self.__data[key]
