import config
import time,os,hashlib,re,base64,pickle,exceptions

class ConfigError(exceptions.StandardError):
	pass

class StoreBase(object):
	@classmethod
	def create(cls,store_type,session_config):
		store_cls = None
		if 'file' == store_type:
			store_cls = FileStore
		elif 'memcache' == store_type:
			store_cls = MemStore
		
		if store_cls is None:
			raise ConfigError('no such store type:%s'%store_type)
		
		s = store_cls(session_config)
		
		# cleanup
		s.cleanup()
		
		return s
		
	def __init__(self,config):
		self.__config = config
		
	def config(self):
		return self.__config
		
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
		directory = self.config()['file_directory']
		path = '%s/%s'%(directory,key)
		if not os.path.isfile(path):
			return value
		f = open(path,'r')
		BUF_SIZE = 1024*24
		c = f.read(BUF_SIZE)
		f.close()
		return c
		
	def __setitem__(self, key, value):
		directory = self.config()['file_directory']
		try:
			os.makedirs( directory )
		except:
			pass
		
		path = '%s/%s'%(directory,key)
		fout = open( path ,'w')
		fout.write( value )
		fout.close()
		
	def __contains__(self,key):
		directory = self.config()['file_directory']
		path = '%s/%s'%(directory,key)
		return os.path.isfile(path)
		
	def cleanup(self):
		directory = self.config()['file_directory']
		timeout = self.config()['timeout']
		now = time.time()
		for f in os.listdir(directory):
			path = os.path.join(directory,f)
			atime = os.stat(path).st_atime
			if now - atime > timeout :
				os.remove(path)

class MemStore(StoreBase):
	def __init__(self,config):
		super(MemStore,self).__init__(config)
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
		self.mc.set( key, value, self.config()['timeout'] )
		
	def __delitem__(self, key):
		self.mc.delete(key)
		
	def cleanup(self):
		pass

class Session(object):
	def __init__(self,application):
		self.__application = application
		self.__store = None
		self.__data = dict()
		
	def start(self):
		cookie_name = config.config['session']['cookie_name']
		aCookie = self.__application.cookie()
		aRequest = self.__application.request()
		self.__store = StoreBase.create(
			store_type = config.config['session']['store_type'],
			session_config = config.config['session']
		)
		
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
					aRequest.remoteAddress(),
					config.config['session']['timeout']
				)
			else:
				self.__data = self.__decodeData(rawdata)
			
			# validate address
			# check expired time
			if aRequest.remoteAddress() != self.get('_remote_address') \
					or time.time() > self.get('_expired'):
				self.__initData(
					aRequest.remoteAddress(),
					config.config['session']['timeout']
				)
			
		# recreate session_id
		if self.__session_id is None:
			self.__session_id = self.__recreate_session_id(
				aRequest.remoteAddress(),
				config.config['session']['secret_key']
			)
			aCookie.add(cookie_name,self.__session_id)
			self.__initData(
				aRequest.remoteAddress(),
				config.config['session']['timeout']
			)
		
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
			
			session_id = hashlib.sha1("%s%s%s%s" %(rand, now, ip, secret_key)).hexdigest()
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
