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