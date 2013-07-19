# -*- coding: utf-8 -*-

import db

class LinkedModel(object):
	__cache = {}

	def __init__(self,sTableName):
		self.__tableName = sTableName
		self.__db = db.Db()
		self.__params = None
		
		# linked data
		self.__clearLinkedData()
		
	def field(self,column,table=None):
		self.__appendLinkedData('field',dict(
			column=column,
			table=table
		))
		return self
		
	def reflectField(self,r):
		'''
		True : 强制反射所有表
		False : 强制不反射任何表
		None/'auto' : 如果有field参数，则不反射；如果没有field参数，则反射
		list() : 仅反射列表中指定的表，表名必须使用alias name
		
		默认为None
		'''
		self.__setLinkedData('reflectField',r)
		return self
		
	def alias(self,a):
		self.__setLinkedData('alias',a)
		return self
		
	def where(self,data = None,**w):
		'''
			设置where参数
			字典的形式
		'''
		if data is None:
			data = w
		else:
			data.update(w)
		self.__setLinkedData('where', data)
		return self
		
	def order(self, field, sequence=None):
		self.__appendLinkedData('order', (field, sequence))
		return self
		
	def limit(self,length,offset=None):
		self.__setLinkedData('limit',dict(length=length,offset=offset))
		return self
		
	def join(self,jointable,alias=None,on=None,jointype='left'):
		if alias is None:
			alias = jointable
		self.__appendLinkedData(
			'join',
			dict(
				jointable=jointable,
				alias=alias,
				on=on,
				jointype = jointype
			)
		)
		return self
		
	def group(self,g):
		self.__appendLinkedData('group',g)
		return self
		
	def select(self, options=[]):
		fieldString = self.__buildFieldString()
		tableString = self.__buildTableString()
		joinString = self.__buildJoinString()
		whereString = self.__buildWhereString()
		orderString = self.__buildOrderString()
		limitString = self.__buildLimitString()
		groupString = self.__buildGroupString()
		
		queryString = "select{options}{field}\nfrom {table}{join}{where}{group}{order}{limit}".format(
			options=' '.join(options),
			field=fieldString,
			table=tableString,
			join=joinString,
			where=whereString,
			group=groupString,
			order=orderString,
			limit=limitString
		)

		res = self.__db.query(queryString, self.__params)
		self.__clearLinkedData()
		return res
		
	def find(self):
		res = self.limit(1).select()
		if len(res) < 1:
			return None
		else:
			return res[0]
		
	def count(self, countField='*'):
		tableString = self.__buildTableString()
		joinString = self.__buildJoinString()
		whereString = self.__buildWhereString()
		groupString = self.__buildGroupString()
		
		queryString = "select count(%s) from %s%s%s%s"%(
			countField,
			tableString,
			joinString,
			whereString,
			groupString
		)
		
		result = self.__db.queryOne(queryString, self.__params)
		self.__clearLinkedData()
		return result[0]
		
	def insert(self,**data):
		columnList = list()
		valueList = list()
		params = dict()
		max_value_length = 0
		for column,value in data.iteritems():
			columnList.append(column)
			if isinstance(value,(list,tuple) ):
				max_value_length = max( max_value_length, len(value) )
				for i, v in enumerate(value):
					key = '%s_%d' % (column, i)
					params[key] = v
			else:
				max_value_length = max(max_value_length, 1)
				params[column] = value
		
		# empty
		if max_value_length <= 0:
			return

		tableString = self.__db.tablePrefix() + self.__tableName

		def get_column_fields(data, column, i):
			if isinstance(data[column], (list, tuple)):
				return '%%(%s_%d)s' % (column, i)
			else:
				return '%%(%s)s' % column

		queryString = "insert into %(table)s (%(columns)s) values %(values)s"%{
			'table' : tableString,
			'columns' : ','.join(columnList),
			'values' : ','.join([
				'( %s )'% ','.join([
					get_column_fields(data, column, i)
					for column in columnList
				])
				for i in range(0,max_value_length)
			])
		}

		n = self.__db.execute(queryString,params)
		insert_id = self.__db.insert_id()
		self.__clearLinkedData()
		return insert_id
		
	def update(self,**data):
		dataString = ''
		dataStringPartedList = list()
		for k,v in data.iteritems():
			if k in self.__getColumnList(self.__tableName):
				param_key = self.__addParam(k, v)
				dataStringPartedList.append(
					'%s=%%(%s)s' % (
						param_key,
						param_key
					)
				)

		dataString = ' ,'.join(dataStringPartedList)
		
		tableString = self.__db.tablePrefix() + self.__tableName
		queryString = "update %(table)s set %(data)s %(where)s" % dict(
			table = tableString,
			data = dataString,
			where = self.__buildWhereString()
		)
		
		n = self.__db.execute(queryString, self.__params)
		self.__clearLinkedData()
		return n

	def found_rows(self):
		res = self.__db.queryOne('select FOUND_ROWS()')
		return res[0]

	def __appendLinkedData(self,name,value):
		if not name in self.__linkedData:
			self.__linkedData[name] = list()
		
		self.__linkedData[name].append( value )
	
	def __setLinkedData(self,name,value):
		self.__linkedData[name] = value
		
	def __getLinkedData(self, name, defaultValue=None):
		return self.__linkedData.get(name, defaultValue)
		
	def __clearLinkedData(self):
		self.__linkedData = dict()
		self.__params = dict()

		# default alias
		self.alias(self.__tableName)
		
	def __getTableNameList(self):
		tableNameList = list()
		tableNameList.append( self.__tableName )
		
		joinData = self.__getLinkedData('join')
		if joinData:
			for join in joinData:
				tableNameList.append( join['jointable'] )
			
		return tableNameList
	
	def __getColumnList(self,tableName):
		if not 'showColumns' in self.__cache:
			self.__cache['showColumns'] = dict()
		
		if not tableName in self.__cache['showColumns']:
			aIter = self.__db.query("SHOW COLUMNS FROM `%s%s`"%(
				self.__db.tablePrefix(),
				tableName
			))
			columnList = list()
		
			for i in aIter:
				columnList.append(i['Field'])
			
			self.__cache['showColumns'][tableName] = columnList
		
		return self.__cache['showColumns'][tableName]
	
	def __getTableAliasList(self):
		tableAliasList = list()
		aliasData = self.__getLinkedData('alias')
		tableAliasList.append( (self.__tableName , aliasData) )
		
		joinData = self.__getLinkedData('join')
		if joinData:
			for join in joinData:
				tableAliasList.append( (join['jointable'] , join['alias'] ) )
				
		return tableAliasList
		
	def __buildFieldString(self):
		reflectFieldData = self.__getLinkedData('reflectField')
		fieldData = self.__getLinkedData('field')
		
		if reflectFieldData is None \
			or reflectFieldData == 'auto':
			if fieldData:
				fieldList = self.__buildFieldListByFieldData( fieldData )
			else:
				fieldList = self.__buildFieldListByColumn()
		elif reflectFieldData == True:
			fieldList = self.__buildFieldListByColumn()
			if fieldData:
				fieldList.extend( self.__buildFieldListByFieldData( fieldData ) )
		elif reflectFieldData == False:
			if fieldData:
				fieldList = self.__buildFieldListByFieldData( fieldData )
			else:
				fieldList = list()
		elif isinstance( reflectFieldData , list ):
			fieldList = self.__buildFieldListByColumn(reflectFieldData)
			if fieldData:
				fieldList.extend( self.__buildFieldListByFieldData( fieldData ) )
			
		fieldString = '\n' + ',\n'.join(fieldList)
		return fieldString
		
	def __buildFieldListByFieldData(self,fieldData):
		fieldStringPartedList = list()
		for f in fieldData:
			if f['table']:
				fieldStringParted = '`%s`.`%s` as `%s.%s`'%(
					f['table'],
					f['column'],
					f['table'],
					f['column']
				)
			else:
				fieldStringParted = f['column']
			fieldStringPartedList.append(fieldStringParted)
		return fieldStringPartedList
		
	def __buildFieldListByColumn(self,tableAliasList=None):
		# table alias
		AllTableAliasList = self.__getTableAliasList()
		
		# build field
		fieldStringPartedList = list()
		for tableName , aliasName in AllTableAliasList:
			if tableAliasList is None or aliasName in tableAliasList:
				for columnName in self.__getColumnList(tableName):
					if tableName == self.__tableName :
						fieldStringParted = '`%s`.`%s`'%(
							aliasName,
							columnName
						)
					else:
						fieldStringParted = '`%s`.`%s` as `%s.%s`'%(
							aliasName,
							columnName,
							aliasName,
							columnName
						)
					
					fieldStringPartedList.append( fieldStringParted )
		
		return fieldStringPartedList
		
	def __buildTableString(self):
		aliasData = self.__getLinkedData('alias')
		tableName = self.__db.tablePrefix() + self.__tableName
		if aliasData:
			tableString = '`%s` as %s'%(tableName,aliasData)
		else:
			tableString = '`%s`'%(tableName)
		
		return tableString
		
	def __buildJoinString(self):
		joinStringPartedList = list()
		joinData = self.__getLinkedData('join')
		tablePrefix = self.__db.tablePrefix()
		if joinData:
			for join in joinData:
				joinStringParted = '%s join `%s`'%(
					join['jointype'],
					tablePrefix+join['jointable'],
				)
				if join['alias']:
					joinStringParted = joinStringParted + ' as %s'%join['alias']
				if join['on']:
					joinStringParted = joinStringParted + ' on (%s)'%join['on']
				joinStringPartedList.append( joinStringParted )
			joinString = "\n" + "\n".join( joinStringPartedList )
		else:
			joinString = ''
		return joinString

	def __buildWherePart(self, key, value):
		if '$str' == key:
			return value
		elif '$or' == key:
			return " OR ".join(
				[self.__buildWhereStringFromData(v) for v in value]
			)
		elif isinstance(value, (basestring, int, long)):
			param_key = self.__addParam(key, value)
			return "%s = %%(%s)s" % (key, param_key)
		elif isinstance(value, tuple):
			relation, realvalue = value
			if 'in' == relation:
				param_key_list = list()
				for i, v in enumerate(realvalue):
					param_key = self.__addParam(
						'%s_%d' % (key, i),
						v
					)
					param_key_list.append(param_key)

				return "%s in %s" % (
					key,
					'(' + ','.join(
						('%%(%s)s' % param_key for param_key in param_key_list)
					) + ')'
				)
			elif relation in ('>', '<', '>=', '<='):
				param_key = self.__addParam(key, realvalue)
				return '%s %s %%(%s)s' % (key, relation, param_key)
			else:
				raise ValueError('no such relation: %s' % relation)
		else:
			raise ValueError(value)

	def __buildWhereStringFromData(self, whereData):
		if whereData:
			return "(" + ") AND (".join(
				[self.__buildWherePart(key, value) for key, value in whereData.iteritems()]
			) + ")"
		else:
			return ''

	def __buildWhereString(self):
		ret = self.__buildWhereStringFromData(
			self.__getLinkedData('where')
		)
		if ret:
			return '\nwhere ' + ret
		else:
			return ''

	def __buildOrderString(self):
		orderData = self.__getLinkedData('order')
		if orderData:
			orderString = "\norder by "+','.join([
				"%s %s" % (field, sequence) if sequence else field
				for field, sequence in orderData
			])
		else:
			orderString = ''
		return orderString
		
	def __buildLimitString(self):
		limitData = self.__getLinkedData('limit')
		if limitData:
			if limitData['offset'] is None:
				limitString = '\nlimit %s' % limitData['length']
			else:
				limitString = '\nlimit %s,%s' % (
					limitData['offset'],
					limitData['length']
				)
		else:
			limitString = ''
		return limitString
		
	def __buildGroupString(self):
		groupData = self.__getLinkedData('group')
		if groupData:
			groupString = '\ngroup by ' + ','.join(groupData)
		else:
			groupString = ''
		return groupString

	def __addParam(self, key, value):
		guess_length = 10

		if key in self.__params:
			for i in range(guess_length):
				guess_key = '%s_%d' % (key, i)
				if not guess_key in self.__params:
					break

			if guess_length - 1 == i:
				raise ValueError('can not guess key for %s' % key)

			self.__params[guess_key] = value
			return guess_key
		else:
			self.__params[key] = value
			return key
