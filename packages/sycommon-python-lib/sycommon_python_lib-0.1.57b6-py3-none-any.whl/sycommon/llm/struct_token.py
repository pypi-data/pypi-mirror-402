from typing import Dict, List, Optional, Any
from langfuse import Langfuse, LangfuseSpan, propagate_attributes
from sycommon.llm.llm_logger import LLMLogger
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import BaseMessage, HumanMessage
from sycommon.llm.llm_tokens import TokensCallbackHandler
from sycommon.logging.kafka_log import SYLogger
from sycommon.tools.env import get_env_var
from sycommon.tools.merge_headers import get_header_value


class StructuredRunnableWithToken(Runnable):
    """带Token统计的Runnable类"""

    def __init__(self, retry_chain: Runnable, langfuse: Optional[Langfuse]):
        super().__init__()
        self.retry_chain = retry_chain
        self.langfuse = langfuse

    def _adapt_input(self, input: Any) -> List[BaseMessage]:
        """适配输入格式"""
        if isinstance(input, list) and all(isinstance(x, BaseMessage) for x in input):
            return input
        elif isinstance(input, BaseMessage):
            return [input]
        elif isinstance(input, str):
            return [HumanMessage(content=input)]
        elif isinstance(input, dict) and "input" in input:
            return [HumanMessage(content=str(input["input"]))]
        else:
            raise ValueError(f"不支持的输入格式：{type(input)}")

    def _get_callback_config(
        self,
        config: Optional[RunnableConfig] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> tuple[RunnableConfig, TokensCallbackHandler]:
        """构建包含Token统计和metadata的回调配置"""
        token_handler = TokensCallbackHandler()

        if config is None:
            processed_config = {"callbacks": [], "metadata": {}}
        else:
            processed_config = config.copy()
            if "callbacks" not in processed_config:
                processed_config["callbacks"] = []
            if "metadata" not in processed_config:
                processed_config["metadata"] = {}

        # 添加 Langfuse metadata
        if trace_id:
            processed_config["metadata"]["langfuse_session_id"] = trace_id
        if user_id:
            processed_config["metadata"]["langfuse_user_id"] = user_id

        callbacks = processed_config["callbacks"]
        if not any(isinstance(cb, LLMLogger) for cb in callbacks):
            callbacks.append(LLMLogger())
        callbacks.append(token_handler)

        callback_types = {}
        unique_callbacks = []
        for cb in callbacks:
            cb_type = type(cb)
            if cb_type not in callback_types:
                callback_types[cb_type] = cb
                unique_callbacks.append(cb)

        processed_config["callbacks"] = unique_callbacks

        return processed_config, token_handler

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs) -> Dict[str, Any]:
        # 获取 trace_id 和 user_id
        trace_id = SYLogger.get_trace_id()
        userid = get_header_value(SYLogger.get_headers(), "x-userid-header")
        syVersion = get_header_value(SYLogger.get_headers(), "s-y-version")
        user_id = userid or syVersion or get_env_var('VERSION')

        # 判断是否启用 Langfuse
        if self.langfuse:
            try:
                with self.langfuse.start_as_current_observation(as_type="span", name="invoke") as span:
                    with propagate_attributes(session_id=trace_id, user_id=user_id):
                        span.update_trace(user_id=user_id, session_id=trace_id)
                        return self._execute_chain(input, config, trace_id, user_id, span)
            except Exception as e:
                # Langfuse 跟踪失败不应阻断业务，降级执行
                SYLogger.error(f"Langfuse 同步跟踪失败: {str(e)}", exc_info=True)
                return self._execute_chain(input, config, trace_id, user_id, None)
        else:
            # 未启用 Langfuse，直接执行业务逻辑
            return self._execute_chain(input, config, trace_id, user_id, None)

    async def ainvoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs) -> Dict[str, Any]:
        # 获取 trace_id 和 user_id
        trace_id = SYLogger.get_trace_id()
        userid = get_header_value(SYLogger.get_headers(), "x-userid-header")
        syVersion = get_header_value(SYLogger.get_headers(), "s-y-version")
        user_id = userid or syVersion or get_env_var('VERSION')

        # 判断是否启用 Langfuse
        if self.langfuse:
            try:
                with self.langfuse.start_as_current_observation(as_type="span", name="ainvoke") as span:
                    with propagate_attributes(session_id=trace_id, user_id=user_id):
                        span.update_trace(user_id=user_id, session_id=trace_id)
                        return await self._aexecute_chain(input, config, trace_id, user_id, span)
            except Exception as e:
                # Langfuse 跟踪失败不应阻断业务，降级执行
                SYLogger.error(f"Langfuse 异步跟踪失败: {str(e)}", exc_info=True)
                return await self._aexecute_chain(input, config, trace_id, user_id, None)
        else:
            # 未启用 Langfuse，直接执行业务逻辑
            return await self._aexecute_chain(input, config, trace_id, user_id, None)

    def _execute_chain(
        self,
        input: Any,
        config: Optional[RunnableConfig],
        trace_id: str,
        user_id: str,
        span: LangfuseSpan
    ) -> Dict[str, Any]:
        """执行实际的调用逻辑 (同步)"""
        try:
            processed_config, token_handler = self._get_callback_config(
                config,
                trace_id=trace_id,
                user_id=user_id
            )

            adapted_input = self._adapt_input(input)
            input_data = {"messages": adapted_input}

            if span:
                span.update_trace(input=input_data)

            structured_result = self.retry_chain.invoke(
                input_data,
                config=processed_config
            )

            if span:
                span.update_trace(output=structured_result)

            token_usage = token_handler.usage_metadata
            structured_result._token_usage_ = token_usage

            return structured_result
        except Exception as e:
            SYLogger.error(f"同步LLM调用失败: {str(e)}", exc_info=True)
            return None

    async def _aexecute_chain(
        self,
        input: Any,
        config: Optional[RunnableConfig],
        trace_id: str,
        user_id: str,
        span: LangfuseSpan
    ) -> Dict[str, Any]:
        """执行实际的调用逻辑 (异步)"""
        try:
            processed_config, token_handler = self._get_callback_config(
                config,
                trace_id=trace_id,
                user_id=user_id
            )

            adapted_input = self._adapt_input(input)
            input_data = {"messages": adapted_input}

            if span:
                span.update_trace(input=input_data)

            structured_result = await self.retry_chain.ainvoke(
                input_data,
                config=processed_config
            )

            if span:
                span.update_trace(output=structured_result)

            token_usage = token_handler.usage_metadata
            structured_result._token_usage_ = token_usage

            return structured_result
        except Exception as e:
            SYLogger.error(f"异步LLM调用失败: {str(e)}", exc_info=True)
            return None
