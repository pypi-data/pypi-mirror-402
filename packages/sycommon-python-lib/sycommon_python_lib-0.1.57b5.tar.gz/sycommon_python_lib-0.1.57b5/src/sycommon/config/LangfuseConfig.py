from pydantic import BaseModel


class LangfuseConfig(BaseModel):
    name: str
    secretKey: str
    publicKey: str
    baseUrl: str
    enable: bool

    @classmethod
    def from_config(cls, server_name: str):
        from sycommon.config.Config import Config
        langfuse_config = Config().get_langfuse_config(server_name)
        return cls(**langfuse_config)
