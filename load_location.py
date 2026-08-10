import os
from dotenv import load_dotenv

load_dotenv(override = False)

def get_env(key : str):
    val = os.getenv(key)
    if not val:
        raise RuntimeError
    return val