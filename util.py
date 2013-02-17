# -*- coding: utf-8 -*-

import urllib
import hashlib
import re
import time

def urlquote(s):
	return urllib.quote(s)
	
def deepmerge(target,source):
	for k in target :
		if k in source:
			if isinstance( target[k] ,dict ):
				if isinstance( source[k] , dict ):
					deepmerge(target[k],source[k])
				else:
					target[k] = source[k]
			else:
				target[k] = source[k]

def md5sum(s):
	m = hashlib.md5()
	m.update(s)
	return m.hexdigest()

def toInt(s,default=None):
	if isinstance(s,(int,long)):
		return s
	if isinstance(s,str):
		re_num = r'^-?[0-9]*$'
		reg = re.compile(re_num)
		if reg.match(s):
			return int(s)
		else:
			return default

def isInt(v):
	return isinstance(v,(int,long))

def timeStamp2Str(t):
	return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t))

def timeStamp2Short(t):
	now = time.localtime()
	sti = time.localtime(t)
	
	if now.tm_year != sti.tm_year:
		return time.strftime('%Y-%m-%d',sti)
	elif now.tm_mon != sti.tm_mon or now.tm_mday != sti.tm_mday:
		return time.strftime('%m月%d日',sti)
	else:
		return time.strftime('%H:%M',sti)
