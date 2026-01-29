from sycommon.llm.llm_logger import LLMLogger
from langchain.chat_models import init_chat_model
from sycommon.config.LLMConfig import LLMConfig
from sycommon.llm.sy_langfuse import LangfuseInitializer
from sycommon.llm.usage_token import LLMWithAutoTokenUsage
from typing import Any


def get_llm(
    model: str = None,
    *,
    streaming: bool = False,
    temperature: float = 0.1,
    **kwargs: Any
) -> LLMWithAutoTokenUsage:
    if not model:
        model = "Qwen2.5-72B"

    llmConfig = LLMConfig.from_config(model)
    if not llmConfig:
        raise Exception(f"无效的模型配置：{model}")

    # 初始化 Langfuse
    langfuse_callbacks, langfuse = LangfuseInitializer.get()
    callbacks = [LLMLogger()] + langfuse_callbacks

    init_params = {
        "model_provider": llmConfig.provider,
        "model": llmConfig.model,
        "base_url": llmConfig.baseUrl,
        "api_key": "-",
        "callbacks": callbacks,
        "temperature": temperature,
        "streaming": streaming,
    }

    init_params.update(kwargs)

    llm = init_chat_model(**init_params)

    if llm is None:
        raise Exception(f"初始化原始LLM实例失败：{model}")

    # 获取kwargs中summary_prompt参数
    summary_prompt: str = kwargs.get("summary_prompt")

    return LLMWithAutoTokenUsage(llm, langfuse, llmConfig, summary_prompt)
