import cgi

class Request(object):
	def __init__(self):
		self.__controllerPath = None
		self.__env = None
		
	def run(self,env):
		self.__env = env
		
		# url path
		path = env.get('PATH_INFO')
		self.__urlPath = path
		qs = env.get('QUERY_STRING')
		if not qs is None and len(qs) > 0 :
			self.__urlPath += '?'+qs
		
		# controller path
		# x must be shorter than 20
		x = path.split('/')[1:21]
		
		def list_get(l,index,defaultValue):
			if len(l) > index and l[index] != '':
				return l[index]
			else:
				return defaultValue
		mod = list_get(x,0,'')
		cls = list_get(x,1,'')
		
		self.__controllerPath = '/%s/%s'%(mod,cls)
		
		# params
		self.__paramDict = dict()
		self.__fileDict = dict()
		
		# path params
		for i in range(2,len(x)-1,2):
			key = x[i]
			value = x[i+1]
			self.__paramDict[ key ] = value
		
		# field storage
		self.__field_storage = cgi.FieldStorage(
			fp=env['wsgi.input'],
			environ=env,
			keep_blank_values=True
		)
		for key in self.__field_storage:
			value = self.__field_storage[key]
			# get last in list
			if isinstance(value,list):
				value = value[-1]
			# file or string
			if value.filename is None:
				self.__paramDict[key] = value.value
			else:
				self.__paramDict[key] = value
		
	def __getattr__(self,key):
		return self.__env.get(key,None)
		
	def rootPath(self):
		return self.SCRIPT_NAME
		
	def urlPath(self):
		return self.__urlPath
		
	def controllerPath(self):
		return self.__controllerPath
		
	def params(self):
		return self.__paramDict
