# split-free-backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](
    https://opensource.org/licenses/MIT
)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](
    https://github.com/psf/black
)
[![Code style: isort](https://img.shields.io/badge/code%20style-isort-%231674b1.svg)](
    https://github.com/PyCQA/isort
)

## How to install

- Create a new virtual environment and activate it

```bash
python -m venv .venv
. .venv/bin/activate
```

- Install in dependencies

```bash
pip install -r requirements/base.txt
```

- As dev, install the dev dependencies and set up the pre-commit
  hooks

```bash
pip install -r requirements/dev.txt
pre-commit install
```

## How to install with docker

### For production or staging environments

1. **Build the Docker image:**

    1. Rename */env/prod-sample* to */env/prod* and edit that file

    1. Rename */env/prod.db-sample* to */env/prod.db* and edit that file

    1. Build the images and run the containers:

        ```bash
        docker-compose -f docker/docker-compose.prod.yaml up -d --build
        ```

    1. Make migrations:

        ```bash
        docker-compose -f docker/docker-compose.prod.yaml exec web python manage.py
        migrate --noinput
        ```

    1. See logs:

        ```bash
        docker-compose -f docker/docker-compose.prod.yaml logs -f
        ```

    1. Shut the container down:

        ```bash
        docker-compose -f docker/docker-compose.prod.yaml down -v
        ```

### For development

1. Rename */env/dev-sample* to */env/dev*

1. **Build the images and run the containers:**

    ```bash
    docker-compose -f docker/docker-compose.dev.yaml up -d --build
    ```
