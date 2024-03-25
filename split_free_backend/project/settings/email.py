# Copyright (c) 2024 SplitFree Org.

import os

EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

NEW_USERS_ACTIVE = os.getenv("NEW_USERS_ACTIVE", False)
