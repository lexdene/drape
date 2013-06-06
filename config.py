''' default config for drape '''

from . import util

__config__ = {
    'system': {
        'debug': 'debug',
        'notfound': '/notfound/Index',
        'default_mod': 'index',
        'default_cls': 'Index',
    },
    'db': {
        'driver': 'mysql',
        'dbname': '',
        'user': '',
        'password': '',
        'host': 'localhost',
        'port': 1433,
        'charset': 'utf8',
        'tablePrefix': '',
    },
    'session': {
        'store_type': 'file',
        'file_directory': 'data/session',
        'cookie_name': 'drape_session_id',
        'timeout': 10 * 24 * 3600,
        'secret_key': util.md5sum('drape_web_framework'),
    },
    'view': {
        'render_func': 'drape.render.jinja2',
    },
    'sae_storage': {
        'domain_name': 'storage'
    }
}


def _update(newconfig):
    ''' update new config into config '''
    util.deepmerge(__config__, newconfig)


def include(new_config_module):
    ''' update config module into config '''
    _update(new_config_module.CONFIG)


def get_value(path):
    '''
        get config value by path
    '''
    path_split = path.split('/')
    config_item = __config__
    for path_part in path_split:
        config_item = config_item.get(path_part, {})
    return config_item
