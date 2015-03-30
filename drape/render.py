import os

from . import config, application

_jinja2_env = None


def jinja2(templatePath, vardict):
    global _jinja2_env
    if _jinja2_env is None:
        import jinja2
        from . import util

        cache_dir = config.JINJA_CACHE_DIR
        template_dir = config.JINJA_TEMPLATE_DIR

        util.mkdir_not_existing(cache_dir)

        _jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            extensions=['jinja2.ext.do'],
            bytecode_cache=jinja2.FileSystemBytecodeCache(cache_dir)
        )

    template_filepath = '%s.html' % templatePath
    template = _jinja2_env.get_template(template_filepath)

    return template.render(**vardict)


def mako(templatePath, vardict):
    template_folder = config.TEMPLATE_DIR
    template_filepath = '%s.html' % templatePath
    from mako.template import Template
    from mako.lookup import TemplateLookup
    mylookup = TemplateLookup(
        directories=[template_folder],
        input_encoding='utf-8',
        output_encoding='utf-8',
        encoding_errors='replace'
    )
    mytemplate = mylookup.get_template(template_filepath)
    return mytemplate.render_unicode(**vardict)


def json(vardict):
    import json
    from datetime import time, datetime, date, timedelta

    class ComplexEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, time):
                return obj.strftime('%H:%M:%S')
            elif isinstance(obj, datetime):
                return obj.strftime('%Y/%m/%d %H:%M:%S')
            elif isinstance(obj, date):
                return obj.strftime('%Y-%m-%d')
            elif isinstance(obj, timedelta):
                return self.default(
                    (datetime.min + obj).time()
                )
            else:
                return super(ComplexEncoder, self).default(obj)

    return json.dumps(vardict, cls=ComplexEncoder)


__render_func_map = {
    'jinja2': jinja2,
    'mako': mako
}


def render(path, variables):
    template = config.DEFAULT_TEMPLATOR
    render_func = __render_func_map[template]
    return render_func(path, variables)
