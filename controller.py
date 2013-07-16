import json
import exceptions

import config

class ControllerError(exceptions.StandardError):
	pass

class InControllerRedirect(ControllerError):
	def __init__(self, path, params):
		super(InControllerRedirect,self).__init__()
		self.path = path
		self.params = params

class PathInvalid(Exception):
	pass

class Controller(object):
	def __init__(self,runbox):
		self.__runbox = runbox

		# path
		mod = self.__module__.split('.')[-1]
		cls = self.__class__.__name__
		self.__path = '/%s/%s'%(mod,cls)

		# vars are for view render
		self.__vars = dict()
		
		self.__templatePath = None
		self.__render_func = None
		
		self.__children = dict()
		self.__parent = None
		
	def setVariable(self,name,value):
		self.__vars[name] = value
		
	def variable(self,name):
		return self.__vars[name]
		
	def path(self):
		return self.__path
		
	def setTemplatePath(self,templatePath):
		self.__templatePath = templatePath
		
	def templatePath(self):
		if self.__templatePath:
			return self.__templatePath
		else:
			return self.__path
		
	def setRenderFunc(self,render_func):
		self.__render_func = render_func
		
	def addChild(self,name,aChildCtrl):
		self.__children[name] = aChildCtrl
		aChildCtrl.setParent(self)
		
	def setParent(self,parent):
		if isinstance(parent,str):
			parent = self.runbox().controller(parent)
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
			c = self.runbox().controller(path)
			
			for k, v in e.params.iteritems():
				c.setVariable(k, v)

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
			render_func = config.get_value('view/render_func')
		else:
			render_func = self.__render_func
		x = render_func.split('.')
		mod = '.'.join(x[0:-1])
		func = x[-1]
		mod = __import__(mod, globals(), locals(), [""])
		func = getattr(mod, func)
		return func(self.templatePath(), self.__vars)
		
	def icRedirect(self, path, params):
		raise InControllerRedirect(path, params)
		
	def params(self):
		return self.request().params()
		
	def session(self):
		return self.runbox().session()
		
	def request(self):
		return self.runbox().request()
		
	def response(self):
		return self.runbox().response()
		
	def runbox(self):
		return self.__runbox

	@classmethod
	def controller(cls, fun):
		return type(
			fun.__name__,
			(cls, ),
			{
				'process': fun,
				'__module__': fun.__module__
			}
		)


class jsonController(Controller):
	def __init__(self,runbox):
		super(jsonController,self).__init__(runbox)
		self.setRenderFunc('drape.render.json')
		
		response = self.response()
		response.set_header('Content-Type', 'application/json; charset=utf-8')
