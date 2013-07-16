import request
import response
import cookie
import session
import config

class RunBox(object):
	def __init__(self,application):
		self.__application = application
		self.__request = None
		self.__response = None
		self.__session = None
		self.__cookie = None
		
		self.__variables = dict()
		
	def request(self):
		if self.__request is None:
			self.__request = request.Request()
		return self.__request
		
	def response(self):
		if self.__response is None:
			self.__response = response.Response()
		return self.__response
		
	def session(self):
		if self.__session is None:
			self.__session = session.Session(self)
			self.__session.run()
		return self.__session
		
	def cookie(self):
		if self.__cookie is None:
			self.__cookie = cookie.Cookie(self)
			self.__cookie.run()
		return self.__cookie
		
	def flush(self):
		# session
		if not self.__session is None:
			self.__session.save()
		
	def controller(self,path,**params):
		def getControllerClsByPath(path):
			x = path.split('/')
			mod = x[1]
			cls = x[2]

			# default mod if empty
			if '' == mod:
				mod = config.get_value('system/default_mod')

			mod = 'app.controller.%s'%mod

			# import module
			try:
				mod = __import__(mod, globals(), locals(), [""])
			except ImportError:
				return None

			# default cls if empty
			if '' == cls:
				cls = getattr(
					mod,
					'DEFAULT_CLS',
					config.get_value('system/default_cls')
				)

			# get class
			cls = getattr(mod, cls, None)
			return cls
			
		def getControllerByPath(path,runbox,params):
			cls = getControllerClsByPath(path)
			if cls is None:
				return None
			return cls(runbox,**params)
			
		return getControllerByPath(path,self,params)
		
	def variables(self):
		return self.__variables
