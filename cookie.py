import time

class Cookie(object):
	def __init__(self,runbox):
		self.__runbox = runbox
		self.__requestdata = dict()
	
	def run(self):
		cookiestr = self.__runbox.request().HTTP_COOKIE
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
		
	def add(self,key,value,path='/',expires=None,domain=None):
		# path can be string or tuple
		if isinstance(path,tuple):
			path,path_type = path
		else:
			path_type='relative'
		
		# expires can be float or tuple
		if isinstance(expires,tuple):
			expires,expires_type = expires
		else:
			expires_type='relative'
		
		if 'relative' == path_type:
			rootPath = self.__runbox.request().rootPath()
			path = rootPath + path
		
		if not expires is None:
			if 'relative' == expires_type:
				expires = float(expires) + time.time()
			else:
				expires = float(expires)
		
		self.__addToHeader(dict(
			key = key,
			value = value,
			path = path,
			expires = expires,
			domain = domain
		))
		
	def __addToHeader(self,cookiedata):
		s = '%(key)s=%(value)s; Path=%(path)s'%cookiedata
		
		if not cookiedata['expires'] is None:
			GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
			time_struct = time.gmtime(cookiedata['expires'])
			cookiedata['expires'] = time.strftime(GMT_FORMAT,time_struct)
			s += '; Expires=%(expires)s'%cookiedata
		
		if not cookiedata['domain'] is None:
			s += '; Domain=%(domain)s'%cookiedata
		
		response = self.__runbox.response()
		response.addHeader(
			'Set-Cookie',
			s,
		)
