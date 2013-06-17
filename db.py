import config

import debug

class DbError(Exception):
	pass

class ConfigError(DbError):
	pass

class Db(object):
	def __init__(self):
		dbconfig = config.get_value('db')
		self.__config = dbconfig
		if dbconfig['driver'] == 'mysql':
			import MySQLdb
			self.__driver = MySQLdb
			self.__conn = MySQLdb.connect(
				host = dbconfig['host'] ,
				port = int(dbconfig['port']) ,
				user = dbconfig['user'] ,
				passwd = dbconfig['password'] ,
				db = dbconfig['dbname'] ,
				charset = dbconfig['charset'],
			)
		else:
			raise ConfigError('no such driver : %s'%dbconfig['driver'])
		
	def tablePrefix(self):
		return self.__config['tablePrefix']
		
	def queryOne(self, sql, params=None):
		cursor = self.__conn.cursor()
		try:
			cursor.execute(sql, params)
			return cursor.fetchone()
		finally:
			if self.__config['log_sql']:
				debug.sql( cursor._last_executed )

	def query(self,sql,params=None):
		cursor=self.__conn.cursor(self.__driver.cursors.DictCursor)
		try:
			cursor.execute(sql, params)
			return cursor.fetchall()
		finally:
			if self.__config['log_sql']:
				debug.sql( cursor._last_executed )
		
	def execute(self,sql,params=None):
		cursor=self.__conn.cursor()
		try:
			cursor.execute(sql, params)
			return cursor.rowcount
		finally:
			if self.__config['log_sql']:
				debug.sql( cursor._last_executed )
		
	def insert_id(self):
		return self.__conn.insert_id()
