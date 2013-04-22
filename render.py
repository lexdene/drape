
_jinja2_env = None
def jinja2(templatePath,vardict):
	global _jinja2_env
	if _jinja2_env is None:
		import jinja2
		import util
		util.mkdir_not_existing('data/jinja_cache')
		_jinja2_env = jinja2.Environment(
			loader = jinja2.FileSystemLoader('app/template'),
			extensions = ['jinja2.ext.do'],
			bytecode_cache = jinja2.FileSystemBytecodeCache('data/jinja_cache')
		)
	
	template_filepath = '%s.html'%templatePath
	template = _jinja2_env.get_template(template_filepath)
	
	return template.render(**vardict)

def mako(templatePath,vardict):
	template_folder = 'app/template'
	template_filepath = '%s.html'%templatePath
	from mako.template import Template
	from mako.lookup import TemplateLookup
	mylookup = TemplateLookup(
		directories=[ template_folder ],
		input_encoding='utf-8',
		output_encoding='utf-8',
		encoding_errors='replace'
	)
	mytemplate = mylookup.get_template( template_filepath )
	return mytemplate.render_unicode(**vardict)

def json(templatePath,vardict):
	import json
	return json.dumps(vardict)
