.PHONY: pypi, tag, test

pypi:
	rm -f dist/*
	python setup.py sdist
	twine upload --config-file=.pypirc dist/*
	make tag

tag:
	git tag $$(python -c "from megaparsy.__about__ import __version__; print __version__")
	git push --tags

test:
	py.test -v -s --ipdb tests/