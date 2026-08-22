from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    admin_ids: str = ""
    bot_secret: str
    api_url: str
    redis_url: str

    # Webhook settings (optional — if not set, falls back to polling)
    webhook_url: str = ""
    webhook_path: str = "/webhook"
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8080

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]


settings = Settings()
