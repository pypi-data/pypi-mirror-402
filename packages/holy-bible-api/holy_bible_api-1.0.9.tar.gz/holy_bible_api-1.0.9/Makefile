clean:
	rm -rf dist

build: clean
	uv build

upload:
	uv version --bump major
	make build
	export PYPI_TOKEN=$$(grep PYPI_TOKEN .env | cut -d '=' -f 2) && \
	uv publish -u __token__ -p $$PYPI_TOKEN
