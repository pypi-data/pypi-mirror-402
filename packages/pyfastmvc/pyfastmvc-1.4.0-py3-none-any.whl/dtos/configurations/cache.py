"""
DTO for cache configuration settings.
"""
from pydantic import BaseModel


class CacheConfigurationDTO(BaseModel):
    """
    DTO for cache configuration.
    Fields:
        host (str): Redis host.
        port (int): Redis port.
        password (str): Redis password.
    """
    host: str
    port: int
    password: str
