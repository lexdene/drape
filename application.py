# -*- coding: utf-8 -*-

# system import
import os
import sys
import traceback
import time

# drape import
import controller
import config
import util
import request
import response
import cookie
import session
import eventCenter

class Application(object):
	__singleton = None
	
	@staticmethod
	def singleton():
		return Application.__singleton
		
	@staticmethod
	def setSingleton(singleton):
		Application.__singleton = singleton
		
	def __init__(self):
		self.__apptype = 'cgi'
		self.__log = None
		self.__eventCenter = None
		self.setSingleton(self)
		self.systemInit()
		
	def systemInit(self):
		'''
		系统级初始化，
		这函数理论上讲应该仅在开机/启动服务器的时候执行一次，以后就不再执行了。
		'''
		config.update(self.edconfig())
		
		# give app a chance to register event handler
		try:
			from app.main import init as appinit
			appinit(self)
		except Exception as e:
			pass
		
	def requestInit(self):
		'''
		请求级初始化，
		这函数在每次请求的时候都会执行一次
		'''
		self.__request = request.Request()
		self.__response = response.Response()
		self.__session = None
		self.__cookie = cookie.Cookie(self)
		
		g = controller.Controller.globalVars()
		g.clear()
		
	def _cleanup(self):
		'''
		请求级清理函数，
		这函数在每次请求结束的时候都会执行一次
		'''
		pass
		
	def start(self):
		self.run()
		
	def run(self,environ):
		try:
			self.requestInit()
			
			# read request params
			self.__request.run(environ)
			self.eventCenter().emit(
				'after_request_run',
				dict(
					application = self,
					request = self.__request
				)
			)
			
			# redirect path without postfix '/'
			if self.__request.REQUEST_URI == self.__request.rootPath():
				self.__response.setStatus('301 Moved Permanently')
				self.response().addHeader('Location',self.__request.rootPath() + '/' )
				return
			
			# init cookie
			self.__cookie.run()
			
			# base header
			self.response().addHeader('Content-Type','text/html; charset=utf-8')
			self.response().addHeader('X-Powered-By','python-drape')
			
			# init controller
			path = self.__request.controllerPath()
			controllerCls = controller.getControllerClsByPath(path)
			if controllerCls is None:
				# notfound
				self.__response.setStatus('404 Not Found')
				
				path = config.config['system']['notfound']
				controllerCls = controller.getControllerClsByPath(path)
				if controllerCls is None:
					self.__response.addHeader('Content-Type','text/plain; charset=utf-8')
					self.__response.setBody('404 Not Found')
					return
			c = controllerCls(path)
			
			# response
			self.__response.setBody(c.run())
			
			# session
			if not self.__session is None:
				self.__session.save()
		except Exception as e:
			self.__response.addHeader('Content-Type','text/plain; charset=utf-8')
			
			body = ''
			if 'debug' == config.config['system']['debug']:
				body += 'controllerPath:%s\n'%self.__request.controllerPath()
				body += traceback.format_exc()
				body += "environ:\n"
				for k,v in environ.iteritems():
					body += "%s => %s\n"%(k,v)
			else:
				body = '500 Internal Server Error\n'
			
			self.__response.setBody(body)
			self.__response.setStatus('500 Internal Server Error')
		
	def edconfig(self):
		return dict()
		
	def apptype(self):
		return self.__apptype
		
	def request(self):
		return self.__request
		
	def response(self):
		return self.__response
		
	def cookie(self):
		return self.__cookie
		
	def session(self):
		if self.__session is None:
			self.__session = session.Session(self)
			self.__session.start()
		return self.__session
		
	def saveUploadFile(self,fileobj,filepath):
		pass
		
	def log(self,type,data):
		if self.__log is None:
			import logging
			self.__log = logging
			dirpath = 'data/log'
			if not os.path.isdir(dirpath):
				os.makedirs(dirpath)
			filepath = dirpath + '/%s.log'%time.strftime('%Y-%m-%d',time.localtime())
			logging.basicConfig(
				filename = filepath,
				level = logging.DEBUG,
				format = '[%(asctime)s] [%(levelname)s] %(message)s'
			)
			logging.addLevelName(logging.DEBUG+5,'SQL')
			
		if 'debug' == type:
			self.__log.debug(data)
		elif 'info' == type:
			self.__log.info(data)
		elif 'warning' == type:
			self.__log.warning(data)
		elif 'error' == type:
			self.__log.error(data)
		elif 'critical' == type:
			self.__log.critical(data)
		elif 'sql' == type:
			self.__log.log(self.__log.DEBUG+5,data)
	
	def eventCenter(self):
		if self.__eventCenter is None:
			self.__eventCenter = eventCenter.EventCenter()
		return self.__eventCenter

class WsgiApplication(Application):
	def __init__(self):
		super(WsgiApplication,self).__init__()
		self.__apptype = 'wsgi'
		
	def start(self):
		return
		
	def __call__(self,environ, start_response):
		self.run(environ)
		
		ret = self.response().body()
		if isinstance(ret, unicode):
			ret = ret.encode('utf-8')
			self.response().addHeader('Content-Length',len(ret))
		elif isinstance(ret, str):
			ret = ret
			self.response().addHeader('Content-Length',len(ret))
		else:
			ret = str(ret)
		
		write = start_response(
			self.response().status(),
			self.response().headers()
		)
		
		self._cleanup()
		return ret
		
	def saveUploadFile(self,fileobj,filepath):
		dirpath = 'static/userupload'
		
		if not os.path.isdir(dirpath):
			os.makedirs(dirpath)
		
		filepath = os.path.join(dirpath,filepath)
		fout = open( filepath ,'w')
		fileobj.file.seek(0)
		fout.write( fileobj.file.read() )
		fout.close()
		return os.path.join(self.request().rootPath(),filepath)

class SaeApplication(WsgiApplication):
	def __init__(self):
		super(SaeApplication,self).__init__()
		self.__apptype = 'sae'
		
	def edconfig(self):
		import sae.const
		config={
			'db' : {
				'dbname' : sae.const.MYSQL_DB ,
				'user' : sae.const.MYSQL_USER ,
				'password' : sae.const.MYSQL_PASS ,
				'host' : sae.const.MYSQL_HOST ,
				'port' : sae.const.MYSQL_PORT,
			},
			'session' : {
				'store_type' : 'memcache',
				'store_args' : None,
			}
		}
		return config
		
	def saveUploadFile(self,fileobj,filepath):
		import sae.storage
		s = sae.storage.Client()
		fileobj.file.seek(0)
		ob = sae.storage.Object(fileobj.file.read())
		domain_name = config.config['sae_storage']['domain_name']
		return s.put(domain_name, filepath, ob)
		
	def log(self,type,data):
		print '[%s] [%s] %s'%(
				util.timeStamp2Str( time.time() ),
				type,
				str(data)
			)
