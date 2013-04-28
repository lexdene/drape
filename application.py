# -*- coding: utf-8 -*-

# system import
import os
import sys
import traceback
import time

# drape import
import controller
import config
import runbox
import eventCenter
import util

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
		# give app a chance to register event handler
		try:
			from app.main import init as appinit
			appinit(self)
		except Exception as e:
			pass
		
	def start(self):
		self.run()
		
	def run(self,environ):
		try:
			aRunBox = runbox.RunBox(self)
			
			# run begin
			self.eventCenter().emit(
				'run_begin',
				dict(
					runbox = aRunBox
				)
			)
			
			# init request and response
			aRequest = aRunBox.request()
			aResponse = aRunBox.response()
			
			# request run
			aRequest.run(environ)
			
			# after request run
			self.eventCenter().emit(
				'after_request_run',
				dict(
					application = self,
					request = aRequest
				)
			)
			
			# redirect path without postfix '/'
			if aRequest.REQUEST_URI == aRequest.rootPath():
				aResponse.setStatus('301 Moved Permanently')
				aResponse.addHeader('Location',aRequest.rootPath() + '/' )
				return
			
			# base header
			aResponse.addHeader('Content-Type','text/html; charset=utf-8')
			aResponse.addHeader('X-Powered-By','python-drape')
			
			# init controller
			path = aRequest.controllerPath()
			c = aRunBox.controller(path)
			if c is None:
				# notfound
				aResponse.setStatus('404 Not Found')
				
				path = config.config['system']['notfound']
				c = aRunBox.controller(path)
				if c is None:
					aResponse.addHeader('Content-Type','text/plain; charset=utf-8')
					aResponse.setBody('404 Not Found')
					return aResponse
			
			# response
			aResponse.setBody(c.run())
			
			# flush
			aRunBox.flush()
			
			# run end
			self.eventCenter().emit(
				'run_end',
				dict(
					runbox = aRunBox
				)
			)
		except Exception as e:
			aResponse.addHeader('Content-Type','text/plain; charset=utf-8')
			
			body = ''
			if 'debug' == config.config['system']['debug']:
				body += 'controllerPath:%s\n'%aRequest.controllerPath()
				body += traceback.format_exc()
				body += "environ:\n"
				for k,v in environ.iteritems():
					body += "%s => %s\n"%(k,v)
			else:
				body = '500 Internal Server Error\n'
			
			aResponse.setBody(body)
			aResponse.setStatus('500 Internal Server Error')
		return aResponse
		
	def apptype(self):
		return self.__apptype
		
	def saveUploadFile(self,fileobj,filepath):
		pass
		
	def log(self,type,data):
		if self.__log is None:
			import logging
			self.__log = logging
			dirpath = 'data/log'
			util.mkdir_not_existing(dirpath)
			filepath = dirpath + '/%s.log'%time.strftime('%Y-%m-%d',time.localtime())
			logging.basicConfig(
				filename = filepath,
				level = logging.DEBUG,
				format = '[%(asctime)s] [%(levelname)s] %(message)s'
			)
			logging.addLevelName(logging.DEBUG+5,'SQL')

		# remove \n
		data = util.to_unicode(data).replace(u'\n',u'\\n')
			
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
		aResponse = self.run(environ)
		
		ret = aResponse.body()
		if isinstance(ret, unicode):
			ret = ret.encode('utf-8')
			aResponse.addHeader('Content-Length',len(ret))
		elif isinstance(ret, str):
			ret = ret
			aResponse.addHeader('Content-Length',len(ret))
		else:
			ret = str(ret)
		
		write = start_response(
			aResponse.status(),
			aResponse.headers()
		)
		
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
		
	def sae_config(self):
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
				time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),
				type,
				str(data)
			)
