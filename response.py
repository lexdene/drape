class Response(object):
	def __init__(self):
		self.__status = '200 OK'
		self.__headers = list()
		self.__body = ''
		
	def setStatus(self,status):
		self.__status = status
		
	def addHeader(self,key,value):
		self.__headers.append((key,value))
		
	def setBody(self,body):
		self.__body = body
		
	def status(self):
		return self.__status
		
	def headers(self):
		return self.__headers
		
	def body(self):
		return self.__body
