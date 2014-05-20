.PHONY: clean-pyc

help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"

clean: clean-pyc

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 ernest

deploy:
	git push heroku master
