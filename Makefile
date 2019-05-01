.PHONY: docs test

clear-coverage:
	rm -f .coverage

all-tests: clear-coverage unit-tests db-tests

integration-tests:
	cd tests/integrationtest; make test

unit-tests:
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/unittests

db-tests:
	transiterclt rebuild-db --yes
	nosetests --with-coverage --cover-package=transiter --rednose -v tests/dbtests

docs:
	cd docs; rm -r build; make html

clean:
	rm -rf *.egg-info build dist .eggs .coverage
	cd tests/integrationtest; rm -rf *.egg-info build dist .eggs

black:
	black {transiter,tests,*py}
