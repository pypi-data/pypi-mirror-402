from pydantic import BaseModel


class SentryConfig(BaseModel):
    name: str
    dsn: str
    enable: bool

    @classmethod
    def from_config(cls, server_name: str):
        from sycommon.config.Config import Config
        sentry_config = Config().get_sentry_config(server_name)
        return cls(**sentry_config)
