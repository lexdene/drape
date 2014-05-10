class EventCenter(object):
    def __init__(self):
        self.__handlers = dict()

    def registerHandler(self,name,fun):
        self.__handlers[name] = fun

    def emit(self,name,params):
        fun = self.__handlers.get(name)
        if not fun is None:
            fun(**params)
