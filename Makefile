install:
	poetry install

package-install:
	python3.9 -m pip install --user dist/*.whl --force-reinstall
	
build:
	poetry build
	
publish:
	poetry publish --dry-run

lint:
	poetry run flake8 page_loader

test:
	poetry run pytest
