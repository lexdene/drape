# -*- coding: utf-8 -*-

import urllib.request, urllib.parse, urllib.error
import hashlib
import re
import functools
import random
import string
import os


def urlquote(s):
    return urllib.parse.quote(s)


def md5sum(s):
    m = hashlib.md5()
    m.update(s.encode('utf-8'))
    return m.hexdigest()


def sha1sum(s):
    hasher = hashlib.sha1()
    hasher.update(s.encode('utf-8'))
    return hasher.hexdigest()


def toInt(s, default=None):
    if isinstance(s, int):
        return s
    if isinstance(s, str):
        re_num = r'^-?[0-9]*$'
        reg = re.compile(re_num)
        if reg.match(s):
            return int(s)
        else:
            return default


def isInt(v):
    return isinstance(v, int)


def random_str(length=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(length))


def mkdir_not_existing(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def tile_list_data(source_list_data):
    target_data = []
    for v in source_list_data:
        target_data.append(_tile_data(v))
    return target_data


def _tile_data(source_data):
    target_data = {}
    for key, value in source_data.items():
        key_parted_list = key.split('.')
        part_data = target_data
        initial = key_parted_list[0:-1]

        for key_parted in initial:
            if not key_parted in part_data:
                part_data[key_parted] = {}
            part_data = part_data[key_parted]

        key_parted = key_parted_list[-1]
        if isinstance(value, dict):
            part_data[key_parted] = _tile_data(value)
        else:
            part_data[key_parted] = value

    return target_data



def pick_dict(source, key_list):
    '''
        source是一个dict
        从source中挑选出在key_list中的元素并重新组成一个新的dict
    '''
    target = dict()

    for key in key_list:
        target[key] = source[key]

    return target
