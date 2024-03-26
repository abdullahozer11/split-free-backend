DEBUG = True

LOGGING["formatters"]["colored"] = {  # type: ignore # noqa: F821
    "()": "colorlog.ColoredFormatter",
    "format": "%(log_color)s%(asctime)s %(levelname)s %(name)s %(bold_white)s%(message)s",
}
LOGGING["loggers"]["core"]["level"] = "DEBUG"  # type: ignore # noqa: F821
LOGGING["handlers"]["console"]["level"] = "DEBUG"  # type: ignore # noqa: F821
LOGGING["handlers"]["console"]["formatter"] = "colored"  # type: ignore # noqa: F821

# Uncomment out the following to use sqlite instead of postgresql
DATABASES = SQLITE_OPTION  # type: ignore # noqa: F821
