from langchain_core.callbacks import AsyncCallbackHandler
from typing import Any, Dict, List
from langchain_core.outputs import GenerationChunk, ChatGeneration
from langchain_core.messages import BaseMessage

from sycommon.logging.kafka_log import SYLogger


class LLMLogger(AsyncCallbackHandler):
    """
    通用LLM日志回调处理器，同时支持：
    - 同步调用（如 chain.invoke()）
    - 异步调用（如 chain.astream()）
    - 聊天模型调用
    """

    # ------------------------------
    # 同步回调方法（处理 invoke 等同步调用）
    # ------------------------------
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        model_name = serialized.get('name', 'unknown')
        SYLogger.info(
            f"[同步] LLM调用开始 | 模型: {model_name} | 提示词数: {len(prompts)}")
        self._log_prompts(prompts)

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any
    ) -> None:
        model_name = serialized.get('name', 'unknown')
        SYLogger.info(
            f"[同步] 聊天模型调用开始 | 模型: {model_name} | 消息组数: {len(messages)}")
        self._log_chat_messages(messages)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        # 处理普通LLM结果
        if hasattr(response, 'generations') and all(
            isinstance(gen[0], GenerationChunk) for gen in response.generations
        ):
            for i, generation in enumerate(response.generations):
                result = generation[0].text
                SYLogger.info(
                    f"[同步] LLM调用结束 | 结果 #{i+1} 长度: {len(result)}")
                self._log_result(result, i+1)
        # 处理聊天模型结果
        elif hasattr(response, 'generations') and all(
            isinstance(gen[0], ChatGeneration) for gen in response.generations
        ):
            for i, generation in enumerate(response.generations):
                result = generation[0].message.content
                SYLogger.info(
                    f"[同步] 聊天模型调用结束 | 结果 #{i+1} 长度: {len(result)}")
                self._log_result(result, i+1)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        if isinstance(error, GeneratorExit):
            SYLogger.info("[同步] LLM生成器正常关闭")
            return
        SYLogger.error(f"[同步] LLM调用出错: {str(error)}")

    # ------------------------------
    # 异步回调方法（处理 astream 等异步调用）
    # ------------------------------
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        model_name = serialized.get('name', 'unknown')
        SYLogger.info(
            f"[异步] LLM调用开始 | 模型: {model_name} | 提示词数: {len(prompts)}")
        self._log_prompts(prompts)

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any
    ) -> None:
        model_name = serialized.get('name', 'unknown')
        SYLogger.info(
            f"[异步] 聊天模型调用开始 | 模型: {model_name} | 消息组数: {len(messages)}")
        self._log_chat_messages(messages)

    async def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        # 处理普通LLM结果
        if hasattr(response, 'generations') and all(
            isinstance(gen[0], GenerationChunk) for gen in response.generations
        ):
            for i, generation in enumerate(response.generations):
                result = generation[0].text
                SYLogger.info(
                    f"[异步] LLM调用结束 | 结果 #{i+1} 长度: {len(result)}")
                self._log_result(result, i+1)
        # 处理聊天模型结果
        elif hasattr(response, 'generations') and all(
            isinstance(gen[0], ChatGeneration) for gen in response.generations
        ):
            for i, generation in enumerate(response.generations):
                result = generation[0].message.content
                SYLogger.info(
                    f"[异步] 聊天模型调用结束 | 结果 #{i+1} 长度: {len(result)}")
                self._log_result(result, i+1)

    async def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        if isinstance(error, GeneratorExit):
            SYLogger.info("[异步] LLM生成器正常关闭")
            return
        SYLogger.error(f"[异步] LLM调用出错: {str(error)}")

    # ------------------------------
    # 共享工具方法（避免代码重复）
    # ------------------------------
    def _log_prompts(self, prompts: List[str]) -> None:
        """记录提示词"""
        for i, prompt in enumerate(prompts):
            SYLogger.info(f"提示词 #{i+1}:\n{prompt}")

    def _log_chat_messages(self, messages: List[List[BaseMessage]]) -> None:
        """记录聊天模型的消息"""
        for i, message_group in enumerate(messages):
            SYLogger.info(f"消息组 #{i+1}:")
            for msg in message_group:
                SYLogger.info(f"  {msg.type}: {msg.content}")

    def _log_result(self, result: str, index: int) -> None:
        """记录结果"""
        SYLogger.info(f"结果 #{index}:\n{result}")
