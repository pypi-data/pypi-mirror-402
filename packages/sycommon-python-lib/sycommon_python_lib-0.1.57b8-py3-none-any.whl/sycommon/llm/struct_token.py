import tiktoken
from typing import Dict, List, Optional, Any
from langfuse import Langfuse, LangfuseSpan, propagate_attributes
from sycommon.llm.llm_logger import LLMLogger
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from sycommon.llm.llm_tokens import TokensCallbackHandler
from sycommon.logging.kafka_log import SYLogger
from sycommon.config.LLMConfig import LLMConfig
from sycommon.tools.env import get_env_var
from sycommon.tools.merge_headers import get_header_value


class StructuredRunnableWithToken(Runnable):
    """
    统一功能 Runnable：Trace追踪 + Token统计 + 自动上下文压缩
    """

    def __init__(
        self,
        retry_chain: Runnable,
        langfuse: Optional[Langfuse] = None,
        llmConfig: Optional[LLMConfig] = None,
        summary_prompt: Optional[str] = None,
        model_name: str = "Qwen2.5-72B",
        enable_compression: bool = True,
        threshold_ratio: float = 0.8
    ):
        super().__init__()
        self.retry_chain = retry_chain
        self.langfuse = langfuse
        self.llmConfig = llmConfig
        self.summary_prompt = summary_prompt
        self.model_name = model_name
        self.enable_compression = enable_compression
        self.threshold_ratio = threshold_ratio

        # 初始化 Tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, messages: List[BaseMessage]) -> int:
        """快速估算 Token 数量"""
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # 每条消息的固定开销
            # 兼容 content 是字符串或者 dict 的情况
            content = message.content
            if isinstance(content, str):
                num_tokens += len(self.encoding.encode(content))
            elif isinstance(content, list):  # 多模态或复杂结构
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        num_tokens += len(self.encoding.encode(item["text"]))
            elif isinstance(content, dict):
                num_tokens += len(self.encoding.encode(str(content)))
        return num_tokens

    async def _acompress_context(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """执行异步上下文压缩"""
        # 策略：保留 System Prompt + 最近 N 条，中间的摘要
        keep_last_n = 1

        # 分离系统消息和对话消息
        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        conversation = [
            m for m in messages if not isinstance(m, SystemMessage)]

        if len(conversation) <= keep_last_n:
            return messages

        to_summarize = conversation[:-keep_last_n]
        keep_recent = conversation[-keep_last_n:]

        # 构造摘要 Prompt
        # 注意：这里直接使用 retry_chain 进行摘要，防止死循环
        summary_content = self.summary_prompt or "请将上下文内容进行摘要，保留关键信息，将内容压缩到原来长度的50%左右，保留关键信息。"
        summary_prompt = [
            SystemMessage(content=summary_content),
            HumanMessage(content=f"历史记录:\n{to_summarize}\n\n摘要:")
        ]

        try:
            SYLogger.info(
                f"🚀 Triggering compression: {len(to_summarize)} messages -> summary")

            # 调用子链生成摘要
            # 【关键】必须清空 callbacks，否则 Langfuse 会递归追踪，导致死循环或噪音
            summary_result = await self.retry_chain.ainvoke(
                {"messages": summary_prompt},
                config=RunnableConfig(callbacks=[])
            )

            summary_text = summary_result.content if hasattr(
                summary_result, 'content') else str(summary_result)

            # 重组消息：System + Summary + Recent
            new_messages = system_msgs + \
                [SystemMessage(
                    content=f"[History Summary]: {summary_text}")] + keep_recent
            return new_messages

        except Exception as e:
            SYLogger.error(
                f"❌ Compression failed: {e}, using original context.")
            return messages

    def _adapt_input(self, input: Any) -> List[BaseMessage]:
        """适配输入格式"""
        if isinstance(input, list) and all(isinstance(x, BaseMessage) for x in input):
            return input
        elif isinstance(input, BaseMessage):
            return [input]
        elif isinstance(input, str):
            return [HumanMessage(content=input)]
        elif isinstance(input, dict) and "messages" in input:
            # 如果已经是标准格式字典，直接提取
            msgs = input["messages"]
            return msgs if isinstance(msgs, list) else [msgs]
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
            processed_config = RunnableConfig(callbacks=[], metadata={})
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

        # 去重
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

            # 【同步模式下不建议触发压缩，因为压缩本身是异步调用 LLM】
            # 如果同步也要压缩，需要用 asyncio.run(...)，这里暂时保持原逻辑直接透传
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

            # 1. 适配输入
            adapted_input = self._adapt_input(input)

            # 2. 检查并执行上下文压缩 (仅在异步模式且开启时)
            if self.enable_compression:
                max_tokens = self.llmConfig.maxTokens
                current_tokens = self._count_tokens(adapted_input)

                if current_tokens > max_tokens * self.threshold_ratio:
                    SYLogger.warning(
                        f"⚠️ Context limit reached: {current_tokens}/{max_tokens}")
                    # 执行压缩，替换 adapted_input
                    adapted_input = await self._acompress_context(adapted_input)

            input_data = {"messages": adapted_input}

            if span:
                span.update_trace(input=input_data)

            # 3. 调用子链
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
