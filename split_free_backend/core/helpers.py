# Copyright (c) 2023 SplitFree Org.

import hashlib
import random
import time


def generate_hash():
    random.seed(time.time())
    return hashlib.sha256(str(random.getrandbits(256)).encode("utf-8")).hexdigest()


def get_auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}
