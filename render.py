def jinja2(templatePath,vardict):
	template_filepath = '%s.html'%templatePath
	import jinja2
	env = jinja2.Environment(
		loader = jinja2.FileSystemLoader('app/template'),
		extensions = ['jinja2.ext.do']
	)
	template = env.get_template(template_filepath)
	
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
