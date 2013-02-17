import application

def debug(data):
	a = application.Application.singleton()
	a.log('debug',data)
