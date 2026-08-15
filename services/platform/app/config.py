from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://swifttrack:swifttrack_dev@localhost:5432/swifttrack"
    cms_url: str = "http://localhost:8001/"
    ros_url: str = "http://localhost:8002"
    wms_host: str = "localhost"
    wms_port: int = 9003
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "swifttrack"
    rabbitmq_password: str = "swifttrack_dev"
    rabbitmq_vhost: str = "/"
    workflow_max_retries: int = 3
    workflow_retry_delay_seconds: int = 5
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
