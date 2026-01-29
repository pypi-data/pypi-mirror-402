from envguard import BaseSettings, guard

class Config(BaseSettings):
    database_host: str
    database_port: int
    api_key: str
    debug: bool = False
    max_connections: int = 100

# Load and validate configuration
config = guard(Config, verbose=False)

# Use your configuration
print(config.database_host)
print(config.database_port)