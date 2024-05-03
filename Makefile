
environment := PDBUFR

setup:
	pre-commit install

default:
	@echo No default

qa:
	pre-commit run --all-files

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
