# -*- coding: utf-8 -*-

import re


def validate_params(params, validators):
    validate_results = dict()
    for key, item in validators.iteritems():
        field = _Field()
        field.value = params.get(key)
        field.params = params

        for validate in item['validates']:
            method_name, args = validate[0], validate[1:]
            method_func = getattr(
                field,
                'validate_%s' % method_name
            )

            # 如果验证通过，返回True，否则返回False
            result = method_func(*args)

            if not result:
                if key not in validate_results:
                    validate_results[key] = []

                validate_results[key].append(validate)

    return validate_results


class _Field(object):
    def validate_notempty(self):
        if self.value is None or self.value == '':
            return False
        else:
            return True

    def validate_len(self, minlen, maxlen):
        if len(self.value) < minlen or len(self.value) > maxlen:
            return False
        else:
            return True

    def validate_equal(self, to_key):
        if self.value != self.params[to_key]:
            return False
        else:
            return True

    _EMAIL_REG = re.compile(
        r'^[-a-zA-Z0-9_]*@[-.a-zA-Z0-9_]*$'
    )

    def validate_email(self):
        if not self._EMAIL_REG.match(self.value):
            return False
        else:
            return True

    _INT_REG = re.compile(
        r'^-?[0-9]*$'
    )

    def validate_int(self):
        if not self._INT_REG.match(self.value):
            return False
        else:
            return True
