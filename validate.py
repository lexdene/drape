# -*- coding: utf-8 -*-

import re

def validate_params(params,validateList):
	for validateItem in validateList:
		key = validateItem['key']
		name = validateItem['name']
		value = params.get(key)
		for validate in validateItem['validates']:
			method = validate[0]
			if 'notempty' == method:
				if value is None:
					return dict(
						result = False,
						msg = u'%s不能为空'%name
					)
			elif 'len' == method:
				if len(value) < validate[1] or len(value) > validate[2]:
					return dict(
						result = False,
						msg = u'%s的长度必须在[%d,%d]之间'%(name,validate[1],validate[2])
					)
			elif 'equal' == method:
				if value != params[validate[1]]:
					return dict(
						result = False,
						msg = u'%s必须要和%s相同'%(name,validate[2])
					)
			elif 'email' == method:
				re_email = r'^[-a-zA-Z0-9_]*@[-.a-zA-Z0-9_]*$'
				reg = re.compile(re_email)
				if not reg.match(value):
					return dict(
						result = False,
						msg = u'%s不符合E-mail格式'%(name)
					)
			elif 'int' == method:
				re_num = r'^-?[0-9]*$'
				reg = re.compile(re_num)
				if not reg.match(str(value)):
					return dict(
						result = False,
						msg = u'%s不符合整数格式'%(name)
					)
			else:
				raise KeyError(method)
	return dict(
		result = True,
		msg = ''
	)
