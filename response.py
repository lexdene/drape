class Response(object):
	def __init__(self):
		self.__status = '200 OK'
		self.__headers = list()
		self.__body = ''
		self.__content_type = 'text/html'

	def setStatus(self, status):
		self.__status = status

	def addHeader(self, key, value):
		self.__headers.append((key, str(value)))

	def setBody(self, body):
		self.__body = body

	def status(self):
		return self.__status

	def headers(self):
		return self.__headers

	def body(self):
		return self.__body

	def setContentType(self, content_type):
		self.__content_type = content_type

	def contentType(self):
		return self.__content_type

	def flush(self):
		self.addHeader('Content-Type', '%s; charset=utf-8' % self.contentType())
		self.addHeader('X-Powered-By', 'python-drape')
