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

- As dev, set the pre-push hook that assures tests are passing before pushing

```bash
cp ./.pre-push.sh ./.git/hooks/pre-push
```

## How to install with docker

### For production or staging environments

1. **Build the Docker image:**

    ```bash
    docker build -f Dockerfile.prod -t split-free-backend-prod .
    ```

    OR

    ```bash
    docker build -f Dockerfile.staging -t split-free-backend-staging .
    ```

2. **Run the Docker container:**

    ```bash
    docker run -p 8000:8000 split-free-backend-prod
    ```

    OR

    ```bash
    docker run -p 8000:8000 split-free-backend-staging
    ```

### For development

1. **Build the Docker image:**

    ```bash
    docker build -f Dockerfile.dev -t split-free-backend-dev .
    ```

2. **Run the Docker container (run the API):**

    ```bash
    docker run -p 8000:8000 split-free-backend-dev
    ```

3. **Alternatively, run other Django commands:**

    - Migrations

    ```bash
    docker run -it split-free-backend-dev python manage.py makemigrations
    docker run -it split-free-backend-dev python manage.py migrate
    ```

    - Tests

    ```bash
    docker run -it split-free-backend-dev python manage.py test
    ```
