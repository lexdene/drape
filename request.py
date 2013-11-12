# -*- coding: utf-8 -*-
''' 封闭请求数据 '''

import cgi

class Request(object):
    ''' request object '''
    def __init__(self, env):
        self.__controller_path = None
        self.env = env

        self.__field_storage = None
        self.__param_dict = dict()
        self.__url_path = ''

        self._run()
        
    def _run(self):
        ''' process params in env '''
        # url path
        path = self.env.get('PATH_INFO')
        self.__url_path = path
        query = self.env.get('QUERY_STRING')
        if not query is None and len(query) > 0 :
            self.__url_path += '?'+query
        
        # controller path
        # path_splits must be shorter than 20
        path_splits = path.split('/')[1:21]
        
        mod = ''
        cls = ''
        try:
            mod, cls = path_splits
        except ValueError:
            pass
        
        self.__controller_path = '%s/%s' % (mod, cls)
        
        # path params
        for i in range(2, len(path_splits) - 1, 2):
            key = path_splits[i]
            value = path_splits[i + 1]
            self.__param_dict[key] = value
        
        # field storage
        self.__field_storage = cgi.FieldStorage(
            fp=self.env['wsgi.input'],
            environ=self.env,
            keep_blank_values=True
        )
        for key in self.__field_storage:
            value = self.__field_storage[key]
            if key[-2:] == '[]':
                real_key = key[:-2]
                if isinstance(value, list):
                    self.__param_dict[real_key] = [
                        v.value if v.filename is None else v
                        for v in value
                    ]
                else:
                    realvalue = value.value if value.filename is None else value
                    self.__param_dict[real_key] = [realvalue]
            else:
                if isinstance(value, list):
                    value = value[-1]
                # file or string
                if value.filename is None:
                    self.__param_dict[key] = value.value
                else:
                    self.__param_dict[key] = value
        
    def __getattr__(self, key):
        return self.env.get(key, None)
        
    def root_path(self):
        ''' WEB ROOT '''
        return self.SCRIPT_NAME
        
    def url_path(self):
        ''' full url '''
        return self.__url_path
        
    def controller_path(self):
        ''' path for controller '''
        return self.__controller_path
        
    def params(self):
        ''' request params '''
        return self.__param_dict
