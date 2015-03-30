first: all

all:

pep8:
	find . -name '*.py' -exec pep8 -r {} \;
