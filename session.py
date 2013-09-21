import time
import hashlib
import re
import base64
import pickle
import os

import config
import util

class ConfigError(Exception):
	pass

class StoreBase(object):
	@classmethod
	def create(cls, store_engine):
		store_class_map = {
			'file': FileStore,
			'memcache': MemStore
		}
		store_cls = store_class_map.get(store_engine)

		if store_cls is None:
			raise ConfigError('no such store type:%s'%store_type)
		
		s = store_cls()
		
		# cleanup
		s.cleanup()
		
		return s
		
	def get(self,key,value=None):
		if key in self:
			return self[key]
		else:
			return value
		
	def cleanup(self):
		raise NotImplementedError
		
	def __contains__(self, key):
		raise NotImplementedError
		
	def __getitem__(self, key):
		raise NotImplementedError
		
	def __setitem__(self, key, value):
		raise NotImplementedError

class FileStore(StoreBase):
	def get(self,key,value=None):
		directory = config.SESSION_FILE_DIRECTORY
		path = '%s/%s'%(directory,key)
		if not os.path.isfile(path):
			return value
		f = open(path,'r')
		BUF_SIZE = 1024*24
		c = f.read(BUF_SIZE)
		f.close()
		return c
		
	def __setitem__(self, key, value):
		directory = config.SESSION_FILE_DIRECTORY
		util.mkdir_not_existing( directory )
		
		path = '%s/%s'%(directory,key)
		fout = open( path ,'w')
		fout.write( value )
		fout.close()
		
	def __contains__(self,key):
		directory = config.SESSION_FILE_DIRECTORY
		path = '%s/%s'%(directory,key)
		return os.path.isfile(path)
		
	def cleanup(self):
		directory = config.SESSION_FILE_DIRECTORY
		timeout = config.SESSION_TIMEOUT
		now = time.time()
		
		if not os.path.isdir(directory):
			return
		for f in os.listdir(directory):
			path = os.path.join(directory,f)
			atime = os.stat(path).st_atime
			if now - atime > timeout :
				os.remove(path)

class MemStore(StoreBase):
	def __init__(self):
		super(MemStore, self).__init__()
		import pylibmc
		self.mc = pylibmc.Client()
		
	def __contains__(self, key):
		data = self.mc.get(key)
		return bool(data)
		
	def __getitem__(self, key):
		value = self.mc.get(key)
		if not value:
			raise KeyError
		else:
			self.mc.set(key,value)
			return value
		
	def __setitem__(self, key, value):
		s = self.mc.get(key)
		self.mc.set(
			key,
			value,
			config.SESSION_TIMEOUT
		)
		
	def __delitem__(self, key):
		self.mc.delete(key)
		
	def cleanup(self):
		pass

class Session(object):
	def __init__(self,runbox):
		self.__runbox = runbox
		self.__store = None
		self.__data = dict()
		
	def run(self):
		cookie_name = config.SESSION_COOKIE_NAME
		aCookie = self.__runbox.cookie()
		aRequest = self.__runbox.request()
		self.__store = StoreBase.create(config.SESSION_STORE_ENGINE)
		
		# read session id from cookie
		self.__session_id = aCookie.get(cookie_name)
		
		# protection against session_id tampering
		if self.__session_id and not self.__valid_session_id(self.__session_id):
			self.__session_id = None
		
		# need recreate data
		if self.__session_id:
			rawdata = self.__store.get(self.__session_id)
			if rawdata is None:
				self.__initData(
					aRequest.REMOTE_ADDR,
					config.SESSION_TIMEOUT
				)
			else:
				self.__data = self.__decodeData(rawdata)
			
			# validate address
			# check expired time
			if aRequest.REMOTE_ADDR != self.get('_remote_address') \
					or time.time() > self.get('_expired'):
				self.__initData(
					aRequest.REMOTE_ADDR,
					config.SESSION_TIMEOUT
				)
			
		# recreate session_id
		if self.__session_id is None:
			self.__session_id = self.__recreate_session_id(
				aRequest.REMOTE_ADDR,
				config.SESSION_SECRET_KEY
			)
			aCookie.add(cookie_name,self.__session_id)
			self.__initData(
				aRequest.REMOTE_ADDR,
				config.SESSION_TIMEOUT
			)
		
	def setCookieAttr(self, path='/', expired=None, domain=None ):
		cookie_name = config.SESSION_COOKIE_NAME
		aCookie = self.__runbox.cookie()
		aCookie.add(cookie_name, self.__session_id, path, expired, domain)
		
	def save(self):
		rawdata = self.__encodeData()
		self.__store[self.__session_id] = rawdata
		
	def iteritems(self):
		for k,v in self.__data.iteritems():
			if k[0] != '_':
				yield (k,v)
		
	def get(self,key,value=None):
		return self.__data.get(key,value)
		
	def set(self,key,value):
		if key is None:
			raise KeyError('key can not be None')
		elif value is None:
			if key in self.__data:
				del self.__data[key]
		else:
			self.__data[key] = value
		
	def remove(self,key):
		if key in self.__data:
			del self.__data[key]
		
	def __valid_session_id(self, session_id):
		rx = re.compile('^[0-9a-fA-F]+$')
		return rx.match(session_id)
		
	def __recreate_session_id(self,ip,secret_key):
		while True:
			rand = os.urandom(16)
			now = time.time()
			
			session_id = hashlib.sha1(
				"%s%s%s%s" %(rand, now, ip, secret_key)
			).hexdigest()
			if session_id not in self.__store:
				break
		return session_id
		
	def __initData(self,remote_address,timeout):
		self.__data = {
			'_remote_address' : remote_address,
			'_expired' : time.time() + timeout
		}
		
	def __decodeData(self,rawdata):
		pickled = base64.decodestring(rawdata)
		return pickle.loads(pickled)
		
	def __encodeData(self):
		pickled = pickle.dumps(self.__data)
		return base64.encodestring(pickled)
