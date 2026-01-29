from sycommon.llm.llm_logger import LLMLogger
from langchain.chat_models import init_chat_model
from sycommon.config.LLMConfig import LLMConfig
from sycommon.llm.sy_langfuse import LangfuseInitializer
from sycommon.llm.usage_token import LLMWithAutoTokenUsage


def get_llm(
    model: str = None,
    streaming: bool = False
) -> LLMWithAutoTokenUsage:
    if not model:
        model = "Qwen2.5-72B"

    llmConfig = LLMConfig.from_config(model)
    if not llmConfig:
        raise Exception(f"无效的模型配置：{model}")

    # 初始化Langfuse
    langfuse_callbacks, langfuse = LangfuseInitializer.get()

    callbacks = [LLMLogger()] + langfuse_callbacks

    llm = init_chat_model(
        model_provider=llmConfig.provider,
        model=llmConfig.model,
        base_url=llmConfig.baseUrl,
        api_key="-",
        temperature=0.1,
        streaming=streaming,
        callbacks=callbacks
    )

    if llm is None:
        raise Exception(f"初始化原始LLM实例失败：{model}")

    return LLMWithAutoTokenUsage(llm, langfuse)
