import time

class Cookie(object):
	def __init__(self,application):
		self.__application = application
		self.__requestdata = dict()
		self.__addCookies = list()
	
	def run(self):
		cookiestr = self.__application.request().cookie()
		if not cookiestr is None:
			partList = cookiestr.split(';')
			for part in partList:
				x = part.split('=',2)
				if len(x) < 2:
					continue
				key = x[0].strip()
				value = x[1].strip()
				
				self.__requestdata[key] = value
		
	def get(self,key,v=None):
		return self.__requestdata.get(key,v)
		
	def iteritems(self):
		return self.__requestdata.iteritems()
		
	def add(self,key,value,path='/',expires=None,
			path_type='relative',expires_type='relative'):
		
		if 'relative' == path_type:
			rootPath = self.__application.request().rootPath()
			path = rootPath + path
		
		if not expires is None:
			if 'relative' == expires_type:
				expires = float(expires) + time.time()
			else:
				expires = float(expires)
		
		self.__addCookies.append(dict(
			key = key,
			value = value,
			path = path,
			expires = expires
		))
		
	def addToHeader(self,response):
		for cookiedata in self.__addCookies:
			if cookiedata['expires'] is None:
				s = '%(key)s=%(value)s; Path=%(path)s'%cookiedata
			else:
				GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
				time_struct = time.gmtime(cookiedata['expires'])
				cookiedata['expires'] = time.strftime(GMT_FORMAT,time_struct)
				s = '%(key)s=%(value)s; Path=%(path)s; Expires=%(expires)s'%cookiedata
			response.addHeader(
				'Set-Cookie',
				s,
			)
