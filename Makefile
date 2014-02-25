lint:
	flake8 dj-stripe tests

test:
	python runtests.py

coverage:
	coverage run --source djstripe runtests.py
	coverage report -m

htmlcov:
	coverage run --source djstripe runtests.py
	coverage html
	open htmlcov/index.html

sync_stripe:
	# plans
	# customers
	#
	python manage.py djstripe_init_plans
	python manage.py djstripe_init_customers
	python manage.py djstripe_sync_customers

migrate:
	python manage.py syncdb

run:
	python manage.py runserver 0.0.0.0:8000
