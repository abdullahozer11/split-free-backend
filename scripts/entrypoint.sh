#!/usr/bin/env bash

set -e

RUN_MANAGE_PY='poetry run python -m split_free_backend.manage'

echo 'Collecting static files...'
$RUN_MANAGE_PY collectstatic --no-input

echo 'Running migrations...'
$RUN_MANAGE_PY migrate --no-input

exec poetry run gunicorn split_free_backend.project.wsgi:application -b 0.0.0.0:8000
