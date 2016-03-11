.PHONY: all test clean
test: pep8 ansible-lint unittest

pep8:
	tox -e pep8 -r

ansible-lint:
	tox -e ansible-lint -r

unittest:
	tox -e unittest -r

clean:
	rm -rf .tox
