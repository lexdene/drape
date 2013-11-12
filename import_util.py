''' utils for import '''
import importlib

def import_obj(name):
    ''' import an obj by name '''
    module_path, class_name = name.rsplit('.', 1)
    module = importlib.import_module(module_path)
    obj = getattr(module, class_name)
    return obj

def import_module(name):
    ''' import module by name '''
    return importlib.import_module(name)
