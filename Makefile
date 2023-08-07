CODE = numpydoclint
CODE_TESTS = tests
LINE_LENGTH = 140
MIN_TEST_COVERAGE = 95

format:
	autoflake --recursive --in-place --remove-all-unused-imports $(CODE) $(CODE_TESTS)
	isort --line-length=$(LINE_LENGTH) $(CODE) $(CODE_TESTS)
	black --line-length=$(LINE_LENGTH) $(CODE) $(CODE_TESTS)

lint:
	flake8 --max-line-length=$(LINE_LENGTH) --show-source $(CODE)
	pylint --max-line-length=$(LINE_LENGTH) $(CODE)
	black --line-length=$(LINE_LENGTH) --check $(CODE) $(CODE_TESTS)
	mypy $(CODE)
	numpydoclint $(CODE) -vv

test:
	pytest --cov=$(CODE) --cov-fail-under=$(MIN_TEST_COVERAGE) $(CODE_TESTS)
