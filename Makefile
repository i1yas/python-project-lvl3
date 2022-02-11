install:
	poetry install

package-install: build
	python3.9 -m pip install --user dist/*.whl --force-reinstall
	
build:
	poetry build
	
publish:
	poetry publish --dry-run

lint:
	poetry run flake8 page_loader

test:
	poetry run pytest -vv

test-coverage:
	poetry run pytest --cov=page_loader -vv
