from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config.settings import REDIS_URL

# Initialize the limiter and explicitly tell the connection pool to use SSL
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL,
    storage_options={
        "ssl_cert_reqs": None  # Disables strict certificate verification for cloud managed instances
    }
)