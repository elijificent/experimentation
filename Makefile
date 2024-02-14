.PHONY: install-requirements
install-requirements:
	pip install -r requirements.txt

update-requirements:
	pip freeze > requirements.txt

.PHONY: format
format:
	isort src tests
	black .

.PHONY: lint
lint:
	isort --check src tests
	black --check .

.PHONY: test
test:
	python -m pytest

# If you delete a file from the requirements folder, removing it and running
# this command will remove it from the environment.
.PHONY: reset-requirements
reset-requirements:
	pip install -r requirements.txt --ignore-installed
