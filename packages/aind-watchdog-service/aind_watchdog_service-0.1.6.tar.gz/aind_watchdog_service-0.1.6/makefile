exe:
	uv sync --extra service --extra publish
	uv run build_watchdog.py

test_exe:
	./dist/aind_watchdog_service.exe -v


pypi-release:
	uv build

lint:
	uvx ruff check
	uvx interrogate --verbose src

test: 
	echo "Unit tests are out of date. Use integration_test.py for now."
# 	uv run --with coverage coverage run -m unittest discover
# 	uvx coverage report