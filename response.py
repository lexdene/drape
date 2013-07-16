OK = '200 OK'
REDIRECT = '301 Moved Permanently'
NOT_FOUND = '404 Not Found'
ERROR = '500 Internal Server Error'


class Response(object):
	def __init__(self):
		self.__status = OK
		self.__headers = dict()
		self.__body = ''

		self.set_header('Content-Type', 'text/html; charset=utf-8')
		self.set_header('X-Powered-By', 'python-drape')

	def setStatus(self, status):
		self.__status = status

	def set_header(self, key, value):
		self.__headers[key] = value

	def add_header(self, key, value):
		if key in self.__headers:
			if not isinstance(self.__headers[key], list):
				self.__headers[key] = [self.__headers[key]]
		else:
			self.__headers[key] = list()

		self.__headers[key].append(value)

	def setBody(self, body):
		self.__body = body

	def status(self):
		return self.__status

	def headers(self):
		for key, value in self.__headers.iteritems():
			if isinstance(value, list):
				for value_item in value:
					yield key, value_item
			else:
				yield key, value

	def body(self):
		return self.__body
