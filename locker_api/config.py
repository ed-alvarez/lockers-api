from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseSettings

VERSION = 3
API_VERSION = f"v{VERSION}"

load_dotenv()


class Settings(BaseSettings):
    # Project
    project_name: str
    environment: str
    MAX_SERIAL_NUMBER_LENGTH: int = 255
    MAX_REQ_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_CSV_RECORDS: int = 500
    TIMEOUT_SECONDS: int = 15
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "%(asctime)s -%(levelname)s - %(module)s:%(funcName)s::ln.%(lineno)s:: >%(message)s<"

    # Route53
    cluster_url: str

    # MQTT
    mqtt_host: str = "516a296b5b2540098a6128cf3901fbd8.s1.eu.hivemq.cloud"
    mqtt_port: int = 8883
    mqtt_user: str = "koloni"
    mqtt_pass: str = "VXH9rtp1udy3vaf.zyj"

    # Database
    database_user: str
    database_password: str
    database_host: str
    database_port: int | str
    database_name: str
    db_pool_size = 83
    web_concurrency = 3
    pool_size = db_pool_size // web_concurrency

    # Redis
    redis_url: str
    cache_seconds: int = 3600  # 1 hour

    # AWS
    aws_region: str

    # S3
    images_bucket: str

    # Cognito
    check_expiration = True
    jwt_header_prefix = "Bearer"
    jwt_header_name = "Authorization"

    cognito_client_secret: str

    access_token_expire_minutes: int = 60 * 12
    refresh_token_expire_minutes: int = 60 * 24 * 180

    # Sentry
    sentry_dsn: str

    # Stripe
    stripe_api_key: str
    stripe_pub_key: str
    stripe_webhook_secret: str

    # Twilio
    twilio_sid: str
    twilio_secret: str
    twilio_phone_number: str
    twilio_messaging_service_sid: str
    twilio_verification_sid: str

    ojmar_messaging_service_sid: str
    ojmar_verification_sid: str

    ups_messaging_service_sid: str
    ups_verification_sid: str

    twilio_sendgrid_api_key: str
    twilio_sendgrid_auth_sender: str

    twilio_sendgrid_ojmar_auth_sender: str
    twilio_sendgrid_ups_auth_sender: str

    # Koloni
    frontend_origin: str

    # FastAPI
    host: str = "0.0.0.0"
    port: int = 5000
    api_endpoint_version: str = API_VERSION

    # JWT
    jwt_secret_key: str

    aws_region: str
    aws_access_key_id: str
    aws_secret_access_key: str

    limit: int
    interval: int

    # PackageX
    packagex_api_url: str
    packagex_api_key: str

    class Config:
        case_sensitive = True
        env_file = ".env"


class LinkaConfig(BaseSettings):
    api_key: str
    secret_key: str
    root_url: str

    class Config:
        env_prefix = "linka_"
        case_sensitive = True
        env_file = ".env"


class SpintlyConfig(BaseSettings):
    client_id: str
    client_secret: str

    class Config:
        env_prefix = "spintly_"
        case_sensitive = True
        env_file = ".env"


class KeyniusConfig(BaseSettings):
    email: str
    password: str
    device_id: str
    sub_key: str
    api_url: str

    class Config:
        env_prefix = "keynius_"
        case_sensitive = True
        env_file = ".env"


class HarborConfig(BaseSettings):
    client_id: str
    client_secret: str
    api_url: str
    login_api_url: str

    class Config:
        env_prefix = "harbor_"
        case_sensitive = True
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_linka_config() -> LinkaConfig:
    return LinkaConfig()


@lru_cache()
def get_spintly_config() -> SpintlyConfig:
    return SpintlyConfig()


@lru_cache()
def get_keynius_config() -> KeyniusConfig:
    """
    Get information about the API credentials to be used for requests
    """
    return KeyniusConfig()


@lru_cache()
def get_harbor_config() -> HarborConfig:
    return HarborConfig()
