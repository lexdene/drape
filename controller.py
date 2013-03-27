import config
import application
import json
import exceptions

def getControllerClsByPath(path):
	x = path.split('/')
	mod = x[1]
	cls = x[2]
	mod = 'app.controller.%s'%mod
	
	# import module
	try:
		mod = __import__(mod, globals(), locals(), [""])
	except ImportError:
		return None
	
	# get class
	if hasattr(mod,cls):
		cls = getattr(mod, cls)
	else:
		cls = None
	
	return cls

def getControllerByPath(path):
	cls = getControllerClsByPath(path)
	return cls(path)

class ControllerError(exceptions.StandardError):
	pass

class InControllerRedirect(ControllerError):
	def __init__(self,path,argv):
		super(InControllerRedirect,self).__init__()
		self.path = path
		self.argv = argv

class Controller(object):
	__globalVars = dict()
	def __init__(self,path,templatePath=None):
		self.__path = path
		self.__vars = dict()
		self.__ctrlParams = None
		
		if templatePath is None:
			templatePath = path
		self.__templatePath = templatePath
		self.__render_func = None
		
		self.__children = dict()
		self.__parent = None
		
	def setVariable(self,name,value):
		self.__vars[name] = value
		
	def variable(self,name):
		return self.__vars[name]
		
	def getVardict(self):
		return self.__vars
		
	@classmethod
	def globalVars(cls):
		return cls.__globalVars
		
	def path(self):
		return self.__path
		
	def setTemplatePath(self,templatePath):
		self.__templatePath = templatePath
		
	def templatePath(self):
		return self.__templatePath
		
	def setRenderFunc(self,render_func):
		self.__render_func = render_func
		
	def addChild(self,name,aChildCtrl):
		self.__children[name] = aChildCtrl
		aChildCtrl.setParent(self)
		
	def setParent(self,parent):
		if isinstance(parent,str):
			parent = getControllerByPath(parent)
		self.__parent = parent
		
	def children(self):
		return self.__children.iteritems()
		
	def run(self):
		for name,aCtrl in self.children():
			self.setVariable(name,aCtrl.render())
		
		try:
			self.process()
			self.postProcess()
		except InControllerRedirect as e:
			path = e.path
			c = getControllerByPath(path)
			c.setCtrlParams(e.argv)
			return c.run()
		
		if not self.__parent is None:
			self.__parent.addChild('body',self)
			return self.__parent.run()
		
		return self.render()
		
	def postProcess(self):
		pass
		
	def process(self):
		pass
		
	def render(self):
		if self.__render_func is None:
			render_func = config.config['view']['render_func']
		else:
			render_func = self.__render_func
		x = render_func.split('.')
		mod = '.'.join(x[0:-1])
		func = x[-1]
		mod = __import__(mod, globals(), locals(), [""])
		func = getattr(mod, func)
		return func(self.__templatePath,self.getVardict())
		
	def icRedirect(self,path,*argv):
		raise InControllerRedirect(path,argv)
		
	def params(self):
		aRequest = application.Application.singleton().request()
		return aRequest.params()
		
	def files(self):
		aRequest = application.Application.singleton().request()
		return aRequest.files()
		
	def saveUploadFile(self,fileobj,filepath):
		return application.Application.singleton().saveUploadFile(fileobj,filepath)
		
	def cookie(self):
		return application.Application.singleton().cookie()
		
	def session(self):
		return application.Application.singleton().session()
		
	def request(self):
		return application.Application.singleton().request()
		
	def addHeader(self,key,value):
		application.Application.singleton().response().addHeader(key,value)
		
	def setCtrlParams(self,params):
		self.__ctrlParams = params
		
	def ctrlParams(self):
		return self.__ctrlParams

class jsonController(Controller):
	def __init__(self,path):
		super(jsonController,self).__init__(path)
		self.setRenderFunc('drape.render.json')
