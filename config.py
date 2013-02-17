import util

config={
	'db' : {
		'driver' : 'mysql' ,
		'dbname' : '' ,
		'user' : '' ,
		'password' : '' ,
		'host' : 'localhost' ,
		'port' : 1433 ,
		'charset' : 'utf8' ,
		'tablePrefix' : '',
	},
	'session' : {
		'store_type' : 'file',
		'file_directory' : 'data/session',
		'cookie_name': 'drape_session_id',
		'timeout': 24*3600,
		'secret_key': util.md5sum('drape_web_framework'),
	},
	'view' : {
		'template_type' : 'jinja2',
	},
	'sae_storage' : dict(
		domain_name = 'storage'
	)
}

def update(newconfig):
	global config
	util.deepmerge(config,newconfig)

try:
	import app.config.config as appconfig
	update(appconfig.config)
except ImportError:
	pass
