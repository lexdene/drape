import re

def pluralize(word):
    return word + 's'


def _underscore_repl(matchobj):
    if matchobj.start(0) > 0:
        return '_' + matchobj.group(0).lower()
    else:
        return matchobj.group(0).lower()


def underscore(word):
    return re.sub(
        '[A-Z]',
        _underscore_repl,
        word
    )
