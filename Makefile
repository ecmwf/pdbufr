
environment := PDBUFR

default:
	@echo No default

code-quality:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	mypy --strict .

code-style:
	black .
	isort .

tests:
	pytest -v --cov=. --cov-report=html README.rst tests

deploy:
	check-manifest .
	python setup.py sdist bdist_wheel

env-create:
	conda env create -n $(environment) -f environment.in.yml
	conda install -n $(environment) -y pytest pytest-cov black flake8 mypy isort wheel
	conda install -n $(environment) -c conda-forge -y check-manifest

env-update:
	conda env update -n $(environment) -f environment.in.yml

testclean:
	$(RM) -r */__pycache__ .coverage .cache tests/.ipynb_checkpoints *.lprof

clean: testclean
	$(RM) -r */*.pyc htmlcov dist build .eggs

distclean: clean
	$(RM) -r *.egg-info


.PHONY: code-quality code-style tests env-create env-update
