import view
import application
import json
import exceptions

def getControllerClsByPath(path):
	x = path.split('/')
	mod = x[1]
	cls = x[2]
	mod = 'app.controller.%s'%mod
	mod = __import__(mod, globals(), locals(), [""])
	cls = getattr(mod, cls)
	
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
	def __init__(self,path):
		self.__path = path
		self.__vars = dict()
		self.__ctrlParams = None
		
	def run(self):
		self.process()
		return self.render()
		
	def process(self):
		pass
		
	def render(self):
		return ''
		
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

class ViewController(Controller):
	def __init__(self,path,templatePath=None):
		super(ViewController,self).__init__(path)
		if templatePath is None:
			templatePath = path
		self.__templatePath = templatePath
		
		aRequest = application.Application.singleton().request()
		self.setVariable('ROOT',aRequest.rootPath())
		
		self.setVariable('ctrl',self)
	
	def setTemplatePath(self,templatePath):
		self.__templatePath = templatePath
		
	def templatePath(self):
		return self.__templatePath
		
	def render(self):
		aView = view.View(self.__templatePath)
		r = aView.render(self.getVardict())
		return r
		
	def setTitle(self,t):
		g = self.globalVars()
		g['title'] = t
		
	def title(self):
		g = self.globalVars()
		return g['title']
		
class NestingController(ViewController):
	def __init__(self,path):
		super(NestingController,self).__init__(path)
		self.__children = dict()
		self.__parent = None
		
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
		except InControllerRedirect as e:
			path = e.path
			c = getControllerByPath(path)
			c.setCtrlParams(e.argv)
			return c.run()
		
		if not self.__parent is None:
			self.__parent.addChild('body',self)
			return self.__parent.run()
		
		return self.render()
		
	def initRes(self):
		g = self.globalVars()
		if 'res' not in g:
			g['res'] = list()
		
		myres = list()
		g['res'].append(myres)
		self.setVariable('res',myres)
		
	def addResByPath(self,type='both'):
		# remove prefix /
		path = self.path()
		
		res = self.variable('res')
		
		if type in ['both','css']:
			res.append(('css%s'%path,'css'))
		if type in ['both','js']:
			res.append(('js%s'%path,'js'))
		
	def icRedirect(self,path,*argv):
		raise InControllerRedirect(path,argv)

class jsonController(Controller):
	def render(self):
		return json.dumps(self.getVardict())
