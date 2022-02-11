install:
	poetry install

package-install: build
	pip install --user dist/*.whl --force-reinstall
	
build:
	poetry build
	
publish:
	poetry publish --dry-run

lint:
	poetry run flake8 page_loader

test:
	poetry run pytest -vv

test-coverage:
	poetry run pytest --cov=page_loader --cov-report=xml -vv
