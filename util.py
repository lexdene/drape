# -*- coding: utf-8 -*-

import urllib
import hashlib
import re
import time
import functools

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
	for k in source:
		if not k in target:
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

def to_unicode(obj, encoding='utf-8', errors='replace'):
    ''' convert a 'str' to 'unicode' '''
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding, errors)
    return obj

def utf8(f):
	@functools.wraps(f)
	def rf(*argc,**argv):
		ret = f(*argc,**argv)
		return to_unicode(ret)
	return rf

@utf8
def timeStamp2Str(t):
	return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t))

@utf8
def timeStamp2Short(t):
	now = time.localtime()
	sti = time.localtime(t)
	
	if now.tm_year != sti.tm_year:
		return time.strftime('%Y-%m-%d',sti)
	elif now.tm_mon != sti.tm_mon or now.tm_mday != sti.tm_mday:
		return time.strftime('%m月%d日',sti)
	else:
		return time.strftime('%H:%M',sti)
