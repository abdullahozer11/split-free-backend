.PHONY: runserver
runserver:
	poetry run python -m split_free_backend.manage runserver

.PHONY: migrate
migrate:
	poetry run python -m split_free_backend.manage migrate

.PHONY: test
test:
	PYTEST_RUNNING=true poetry run pytest -v -rs -n auto --show-capture=no
    export PYTEST_RUNNING=false

.PHONY: install
install:
	poetry install

.PHONY: migrations
migrations:
	poetry run python -m split_free_backend.manage makemigrations

.PHONY: install-pre-commit
install-pre-commit:
	poetry run pre-commit uninstall; poetry run pre-commit install

.PHONY: superuser
superuser:
	poetry run python -m split_free_backend.manage createsuperuser

.PHONY: lint
lint:
	poetry run pre-commit run --all-files

.PHONY: shell
shell:
	poetry run python -m split_free_backend.manage shell

.PHONY: lock
lock:
	poetry lock

.PHONY: up-dependencies-only
up-dependencies-only:
	test -f .env || touch .env
	docker-compose -f docker-compose.dev.yaml up --force-recreate db

.PHONY: update
update: install migrate install-pre-commit ;

.PHONY: build-prod
build-prod:
	docker-compose -f docker-compose.yaml up -d --build

.PHONY: build-dev-db
build-dev-db:
	docker-compose -f docker-compose.dev.yaml up -d --build

.PHONY: init-local-settings
init-local-settings:
	mkdir -p local
	cp split_free_backend/project/settings/templates/settings.dev.py ./local/settings.dev.py
	cp split_free_backend/project/settings/templates/settings.prod.py ./local/settings.prod.py
	cp split_free_backend/project/settings/templates/settings.unittests.py ./local/settings.unittests.py

.PHONY: collectstatic
collectstatic:
	poetry run python -m split_free_backend.manage collectstatic --no-input
