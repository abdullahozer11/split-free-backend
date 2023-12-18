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

## Dockerfiles

### Dockerfile.prod
This Dockerfile is designed for production deployments. To use this Dockerfile, follow these steps:

1. **Build the Docker image:**
    ```bash
    docker build -f Dockerfile.prod -t your-image-name .
    ```

2. **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 your-image-name
    ```

Replace `your-image-name` with the desired name for your Docker image.

### Dockerfile.staging
This Dockerfile is tailored for staging. To utilize this Dockerfile, follow these instructions:

1. **Build the Docker image:**
    ```bash
    docker build -f Dockerfile.staging -t your-staging-image-name .
    ```

2. **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 your-staging-image-name
    ```

Replace `your-staging-image-name` with the desired name for your staging Docker image.
