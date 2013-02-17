import config
import exceptions

class DbError(exceptions.StandardError):
	pass

class ConfigError(DbError):
	pass

class Db(object):
	def __init__(self):
		dbconfig = config.config['db']
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
		
	def _conn(self):
		return self.__conn
		
	def query(self,sql,params=None):
		cursor=self.__conn.cursor(self.__driver.cursors.DictCursor)
		n=cursor.execute(sql,params)
		return cursor.fetchall()
		
	def execute(self,sql,params=None):
		cursor=self.__conn.cursor()
		n = cursor.execute(sql,params)
		return n
		
	def insert_id(self):
		return self.__conn.insert_id()
		
	def commit(self):
		return self.__conn.commit()
