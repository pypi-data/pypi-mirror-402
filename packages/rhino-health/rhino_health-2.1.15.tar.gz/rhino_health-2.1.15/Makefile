format:
	python -m black .
	python -m isort .

lint:
	python -m black --check --diff .
	python -m isort --check --diff .

test:
	RHINO_SDK_FORBID_EXTRA_RESULT_FIELDS=1 python -m pytest -m "not local" --ignore=/out

coverage:
	RHINO_SDK_FORBID_EXTRA_RESULT_FIELDS=1 python -m coverage run \
	-m pytest  -m "not local" --ignore=/out
build:
	rm -rf ./dist
	hatch build

.PHONY: lint format test

publish:
	./commands/publish.sh

local:
	./commands/local.sh
