from typing import Any
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs.llm_result import LLMResult
from sycommon.logging.kafka_log import SYLogger


class TokensCallbackHandler(AsyncCallbackHandler):
    """
    继承AsyncCallbackHandler的Token统计处理器
    """

    def __init__(self):
        super().__init__()
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.usage_metadata = {}
        self.reset()

    def reset(self):
        """重置Token统计数据"""
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.usage_metadata = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }

    # ========== 同步回调方法（兼容签名） ==========
    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any,
    ) -> None:
        """同步LLM调用结束时的回调"""
        self._parse_token_usage(response)

    # ========== 异步回调方法（兼容签名） ==========
    async def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any,
    ) -> None:
        """异步LLM调用结束时的回调"""
        self._parse_token_usage(response)

    def _parse_token_usage(self, response: LLMResult) -> None:
        """
        通用Token解析逻辑，不依赖特定类结构
        兼容各种LLM响应格式
        """
        try:
            # 情况1: 标准LangChain响应（有llm_output属性）
            if response.llm_output:
                llm_output = response.llm_output
                self._parse_from_llm_output(llm_output)

            # 情况2: 包含generations的响应
            elif response.generations:
                self._parse_from_generations(response.generations)

            # 计算总Token
            if self.total_tokens <= 0:
                self.total_tokens = self.input_tokens + self.output_tokens

            # 更新metadata
            self.usage_metadata = {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.total_tokens
            }

            SYLogger.debug(
                f"Token统计成功 - 输入: {self.input_tokens}, 输出: {self.output_tokens}")

        except Exception as e:
            SYLogger.warning(f"Token解析失败: {str(e)}", exc_info=True)
            self.reset()

    def _parse_from_llm_output(self, llm_output: dict) -> None:
        """从llm_output字典解析Token信息"""
        if not isinstance(llm_output, dict):
            return

        # OpenAI标准格式
        if 'token_usage' in llm_output:
            token_usage = llm_output['token_usage']
            self.input_tokens = token_usage.get(
                'prompt_tokens', token_usage.get('input_tokens', 0))
            self.output_tokens = token_usage.get(
                'completion_tokens', token_usage.get('output_tokens', 0))
            self.total_tokens = token_usage.get('total_tokens', 0)

        # 直接包含Token信息
        else:
            self.input_tokens = llm_output.get(
                'input_tokens', llm_output.get('prompt_tokens', 0))
            self.output_tokens = llm_output.get(
                'output_tokens', llm_output.get('completion_tokens', 0))
            self.total_tokens = token_usage.get('total_tokens', 0)

    def _parse_from_generations(self, generations: list) -> None:
        """从generations列表解析Token信息"""
        if not isinstance(generations, list) or len(generations) == 0:
            return

        # 遍历generation信息
        for gen_group in generations:
            for generation in gen_group:
                if hasattr(generation, 'generation_info') and generation.generation_info:
                    gen_info = generation.generation_info
                    self.input_tokens = gen_info.get(
                        'input_tokens', gen_info.get('prompt_tokens', 0))
                    self.output_tokens = gen_info.get(
                        'output_tokens', gen_info.get('completion_tokens', 0))
                    self.total_tokens = gen_info.get('total_tokens', 0)
                    return
