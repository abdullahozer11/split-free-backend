DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sfree",
        "USER": "sfree",
        "PASSWORD": "sfree",
        "HOST": "localhost",
        "PORT": "5432",
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 0,
    }
}

SQLITE_OPTION = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # type: ignore # noqa: F821
        "USER": "sfree",
        "PASSWORD": "sfree",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
