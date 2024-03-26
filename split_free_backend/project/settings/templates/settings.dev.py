DEBUG = True
SECRET_KEY = "django-insecure-=!%dlpgnc+4mk7+2h!l4&x^3)r+q4+=nz@y3k&e)8gg^gtgqkn"

LOGGING["formatters"]["colored"] = {  # type: ignore # noqa: F821
    "()": "colorlog.ColoredFormatter",
    "format": "%(log_color)s%(asctime)s %(levelname)s %(name)s %(bold_white)s%(message)s",
}
LOGGING["loggers"]["core"]["level"] = "DEBUG"  # type: ignore # noqa: F821
LOGGING["handlers"]["console"]["level"] = "DEBUG"  # type: ignore # noqa: F821
LOGGING["handlers"]["console"]["formatter"] = "colored"  # type: ignore # noqa: F821

# Uncomment the following to use sqlite instead of postgresql
DATABASES = SQLITE_OPTION  # type: ignore # noqa: F821

# the following activates new user without email verification
NEW_USERS_ACTIVE = False

# in case email verification is needed email host password must be set
# EMAIL_HOST_USER = "split.free.org@gmail.com"
# EMAIL_HOST_PASSWORD = NotImplemented
