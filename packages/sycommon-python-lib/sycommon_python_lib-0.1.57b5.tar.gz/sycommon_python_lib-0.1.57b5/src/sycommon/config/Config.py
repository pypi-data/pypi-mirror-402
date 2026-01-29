import yaml


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    def __init__(self, config_file='app.yaml'):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.MaxBytes = self.config.get('MaxBytes', 209715200)
        self.Timeout = self.config.get('Timeout', 600000)
        self.MaxRetries = self.config.get('MaxRetries', 3)
        self.llm_configs = []
        self.embedding_configs = []
        self.reranker_configs = []
        self.sentry_configs = []
        self.langfuse_configs = []
        self._process_config()

    def get_llm_config(self, model_name):
        for llm in self.llm_configs:
            if llm.get('model') == model_name:
                return llm
        raise ValueError(f"No configuration found for model: {model_name}")

    def get_embedding_config(self, model_name):
        for llm in self.embedding_configs:
            if llm.get('model') == model_name:
                return llm
        raise ValueError(f"No configuration found for model: {model_name}")

    def get_reranker_config(self, model_name):
        for llm in self.reranker_configs:
            if llm.get('model') == model_name:
                return llm
        raise ValueError(f"No configuration found for model: {model_name}")

    def get_sentry_config(self, name):
        for sentry in self.sentry_configs:
            if sentry.get('name') == name:
                return sentry
        raise ValueError(f"No configuration found for server: {name}")

    def get_langfuse_config(self, name):
        for langfuse in self.langfuse_configs:
            if langfuse.get('name') == name:
                return langfuse
        raise ValueError(f"No configuration found for server: {name}")

    def _process_config(self):
        llm_config_list = self.config.get('LLMConfig', [])
        for llm_config in llm_config_list:
            try:
                # 延迟导入 LLMConfigModel
                from sycommon.config.LLMConfig import LLMConfig
                validated_config = LLMConfig(**llm_config)
                self.llm_configs.append(validated_config.model_dump())
            except ValueError as e:
                print(f"Invalid LLM configuration: {e}")

        embedding_config_list = self.config.get('EmbeddingConfig', [])
        for embedding_config in embedding_config_list:
            try:
                from sycommon.config.EmbeddingConfig import EmbeddingConfig
                validated_config = EmbeddingConfig(**embedding_config)
                self.embedding_configs.append(validated_config.model_dump())
            except ValueError as e:
                print(f"Invalid LLM configuration: {e}")

        reranker_config_list = self.config.get('RerankerConfig', [])
        for reranker_config in reranker_config_list:
            try:
                from sycommon.config.RerankerConfig import RerankerConfig
                validated_config = RerankerConfig(**reranker_config)
                self.reranker_configs.append(validated_config.model_dump())
            except ValueError as e:
                print(f"Invalid LLM configuration: {e}")

        sentry_config_list = self.config.get('SentryConfig', [])
        for sentry_config in sentry_config_list:
            try:
                from sycommon.config.SentryConfig import SentryConfig
                validated_config = SentryConfig(**sentry_config)
                self.sentry_configs.append(validated_config.model_dump())
            except ValueError as e:
                print(f"Invalid Sentry configuration: {e}")

    def set_attr(self, share_configs: dict):
        self.config = {**self.config, **
                       share_configs.get('llm', {}), **share_configs}
        self._process_config()
