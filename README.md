# split-free-backend

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

- (Optional) as dev, install the dev dependencies and set up the pre-commit
  hooks

```bash
pip install -r requirements/dev.txt
pre-commit install
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
