
environment := PDBUFR

setup:
	pre-commit install

default:
	@echo No default

qa:
	pre-commit run --all-files
# mypy --strict .

unit-tests:
	pytest -v --cov=. --cov-report=html README.rst tests

conda-env-update:
	$(CONDA) env update $(CONDAFLAGS) -f environment.yml

docker-build:
	docker build -t $(PROJECT) .

docker-run:
	docker run --rm -ti -v $(PWD):/srv $(PROJECT)

template-update:
	pre-commit run --all-files cruft -c .pre-commit-config-weekly.yaml

docs-build:
	cd docs && rm -fr _api && make clean && make html



# tests:
# 	pytest -v --cov=. --cov-report=html README.rst tests

# deploy:
# 	check-manifest .
# 	python setup.py sdist bdist_wheel

# env-create:
# 	conda env create -n $(environment) -f environment.in.yml
# 	conda install -n $(environment) -y pytest pytest-cov black flake8 mypy isort wheel
# 	conda install -n $(environment) -c conda-forge -y check-manifest

# env-update:
# 	conda env update -n $(environment) -f environment.in.yml

# testclean:
# 	$(RM) -r */__pycache__ .coverage .cache tests/.ipynb_checkpoints *.lprof

# clean: testclean
# 	$(RM) -r */*.pyc htmlcov dist build .eggs

# distclean: clean
# 	$(RM) -r *.egg-info


# docs-build:
# 	cd docs && rm -fr _api && make clean && make html


# .PHONY: code-quality code-style tests env-create env-update
