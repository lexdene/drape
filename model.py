# -*- coding: utf-8 -*-

import db

class LinkedModel(object):
	__cache = {}

	def __init__(self,sTableName):
		self.__tableName = sTableName
		self.__db = db.Db()
		
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
		
	def order(self,w):
		self.__appendLinkedData('order',w)
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
		
	def select(self):
		fieldString = self.__buildFieldString()
		tableString = self.__buildTableString()
		joinString = self.__buildJoinString()
		whereString = self.__buildWhereString()
		orderString = self.__buildOrderString()
		limitString = self.__buildLimitString()
		groupString = self.__buildGroupString()
		
		queryString = "select\n%s\nfrom %s\n%s\nwhere %s\n%s\n%s\n%s"%(
			fieldString,
			tableString,
			joinString,
			whereString,
			groupString,
			orderString,
			limitString
		)
		
		paramsData = self.__getLinkedData('params')
		if paramsData is None:
			paramsData = list()
		self.__clearLinkedData()
		return self.__db.query(queryString,dict(paramsData))
		
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
		
		queryString = "select count(%s) from %s \n%s \nwhere %s\n%s"%(
			countField,
			tableString,
			joinString,
			whereString,
			groupString
		)
		
		paramsData = self.__getLinkedData('params')
		if paramsData is None:
			paramsData = list()
		self.__clearLinkedData()

		result = self.__db.queryOne(queryString,dict(paramsData))
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

		self.__clearLinkedData()

		n = self.__db.execute(queryString,params)
		insert_id = self.__db.insert_id()
		return insert_id
		
	def update(self,**data):
		dataString = ''
		dataStringPartedList = list()
		for k,v in data.iteritems():
			if k in self.__getColumnList(self.__tableName):
				dataStringPartedList.append('%s=%%(%s)s'%(k,k))
				self.__appendLinkedData('params',(k,v))
		dataString = ' ,'.join(dataStringPartedList)
		
		tableString = self.__db.tablePrefix() + self.__tableName
		queryString = "update %(table)s set %(data)s where %(where)s"%dict(
			table = tableString,
			data = dataString,
			where = self.__buildWhereString()
		)
		
		paramsData = self.__getLinkedData('params')
		if paramsData is None:
			paramsData = list()
		self.__clearLinkedData()
		
		n = self.__db.execute(queryString,dict(paramsData))
		return n
		
	def __appendLinkedData(self,name,value):
		if not name in self.__linkedData:
			self.__linkedData[name] = list()
		
		self.__linkedData[name].append( value )
	
	def __setLinkedData(self,name,value):
		self.__linkedData[name] = value
		
	def __getLinkedData(self,name):
		return self.__linkedData.get(name, None)
		
	def __clearLinkedData(self):
		self.__linkedData = dict()
		
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
			
		fieldString = ',\n'.join(fieldList)
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
		joinString = " \n".join( joinStringPartedList )
		return joinString

	def __buildWherePart(self, key, value):
		if '$str' == key:
			return value
		elif '$or' == key:
			return " OR ".join(
				[self.__buildWhereStringFromData(v) for v in value]
			)
		elif isinstance(value, (basestring, int, long)):
			self.__appendLinkedData('params', (key, value))
			return "%s = %%(%s)s" % (key, key)
		elif isinstance(value, tuple):
			relation, realvalue = value
			if 'in' == relation:
				for i, v in enumerate(realvalue):
					self.__appendLinkedData(
						'params',
						(
							'%s_%d' % (key, i),
							v
						)
					)
				return "%s in %s" % (
					key,
					'(' + ','.join(
						('%%(%s_%d)s' % (key, i) for i, v in enumerate(realvalue))
					) + ')'
				)
			elif relation in ('>', '<', '>=', '<='):
				self.__appendLinkedData('params', (key, realvalue))
				return '%s %s %%(%s)s' % (key, relation, key)
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
			return '1'

	def __buildWhereString(self):
		return self.__buildWhereStringFromData(
			self.__getLinkedData('where')
		)

	def __buildOrderString(self):
		orderData = self.__getLinkedData('order')
		if orderData:
			orderString = "order by "+','.join( orderData )
		else:
			orderString = ''
		return orderString
		
	def __buildLimitString(self):
		limitData = self.__getLinkedData('limit')
		if limitData:
			if limitData['offset'] is None:
				limitString = 'limit %s'%limitData['length']
			else:
				limitString = 'limit %s,%s'%(limitData['offset'],limitData['length'])
		else:
			limitString = ''
		return limitString
		
	def __buildGroupString(self):
		groupData = self.__getLinkedData('group')
		if groupData:
			groupString = 'group by '+','.join( groupData )
		else:
			groupString = ''
		return groupString
