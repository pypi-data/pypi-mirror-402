import os
from dotenv import load_dotenv

load_dotenv()


def env(key: str, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Missing environment variable: {key}")
    return value


DATABASE_URL = env("DATABASE_URL")
SECRET_KEY = env("SECRET_KEY")
JWT_ALGORITHM = env("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(env("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

REDIS_URL = env("REDIS_URL", "redis://redis:6379/0")
