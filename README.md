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
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-%231674b1.svg)](
https://github.com/PyCQA/flake8
)

## How to install

- Install Poetry

```bash
pip install poetry
```

- Install dependencies

```bash
make install
```

- As dev, set up the pre-commit hooks

```bash
make install-pre-commit
```

## How to install with docker

### For production

1. Copy prod settings to local folder and adjust if needed:

    ```bash
    make copy-prod-settings
    ```

2. Build the images and run the containers:

    ```bash
    make build-prod
    ```

### For development

1. Copy dev settings to local folder and adjust if needed:

```bash
make copy-dev-settings
```

2. **Build the db image and run the container:**

```bash
make build-dev-db
```

3. Run Django server on localhost

```bash
make migrate
make runserver
```

### Testing

```bash
make test
```
