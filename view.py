import config

class View(object):
	def __init__(self,path):
		self.__path = path
		
	def render(self,vardict):
		template_type = config.config['view']['template_type']
		template_folder = 'app/template'
		template_filepath = '%s.html'%self.__path 
		if 'mako' == template_type:
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
		elif 'jinja2' == template_type:
			import jinja2
			env = jinja2.Environment(loader = jinja2.FileSystemLoader('app/template'))
			template = env.get_template(template_filepath)
			
			def do(a):
				return ''
			vardict['do'] = do
			return template.render(**vardict)
