from typing import Type, List, Optional, Callable
from langfuse import Langfuse
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, ValidationError, Field
from sycommon.llm.struct_token import StructuredRunnableWithToken


class LLMWithAutoTokenUsage(BaseChatModel):
    """自动为结构化调用返回token_usage的LLM包装类"""
    llm: BaseChatModel = Field(default=None)
    langfuse: Optional[Langfuse] = Field(default=None, exclude=True)

    def __init__(self, llm: BaseChatModel, langfuse: Langfuse, **kwargs):
        super().__init__(llm=llm, langfuse=langfuse, **kwargs)

    def with_structured_output(
        self,
        output_model: Type[BaseModel],
        max_retries: int = 3,
        is_extract: bool = False,
        override_prompt: ChatPromptTemplate = None,
        custom_processors: Optional[List[Callable[[str], str]]] = None,
        custom_parser: Optional[Callable[[str], BaseModel]] = None
    ) -> Runnable:
        """返回支持自动统计Token的结构化Runnable"""
        parser = PydanticOutputParser(pydantic_object=output_model)

        # 提示词模板
        accuracy_instructions = """
        字段值的抽取准确率（0~1之间），评分规则：
        1.0（完全准确）：直接从原文提取，无需任何加工，且格式与原文完全一致
        0.9（轻微处理）：数据来源明确，但需进行格式标准化或冗余信息剔除（不改变原始数值）
        0.8（有限推断）：数据需通过上下文关联或简单计算得出，仍有明确依据
        0.8以下（不可靠）：数据需大量推测、存在歧义或来源不明，处理方式：直接忽略该数据，设置为None
        """

        if is_extract:
            prompt = ChatPromptTemplate.from_messages([
                MessagesPlaceholder(variable_name="messages"),
                HumanMessage(content=f"""
                请提取信息并遵循以下规则：
                1. 准确率要求：{accuracy_instructions.strip()}
                2. 输出格式：{parser.get_format_instructions()}
                """)
            ])
        else:
            prompt = override_prompt or ChatPromptTemplate.from_messages([
                MessagesPlaceholder(variable_name="messages"),
                HumanMessage(content=f"""
                输出格式：{parser.get_format_instructions()}
                """)
            ])

        # 文本处理函数
        def extract_response_content(response: BaseMessage) -> str:
            try:
                return response.content
            except Exception as e:
                raise ValueError(f"提取响应内容失败：{str(e)}") from e

        def strip_code_block_markers(content: str) -> str:
            try:
                return content.strip("```json").strip("```").strip()
            except Exception as e:
                raise ValueError(f"移除代码块标记失败：{str(e)}") from e

        def normalize_in_json(content: str) -> str:
            try:
                return content.replace("None", "null").replace("none", "null").replace("NONE", "null").replace("''", '""')
            except Exception as e:
                raise ValueError(f"JSON格式化失败：{str(e)}") from e

        def default_parse_to_pydantic(content: str) -> BaseModel:
            try:
                return parser.parse(content)
            except (ValidationError, ValueError) as e:
                raise ValueError(f"解析结构化结果失败：{str(e)}") from e

        # ========== 构建处理链 ==========
        base_chain = prompt | self.llm | RunnableLambda(
            extract_response_content)

        # 文本处理链
        process_runnables = custom_processors or [
            RunnableLambda(strip_code_block_markers),
            RunnableLambda(normalize_in_json)
        ]
        process_chain = base_chain
        for runnable in process_runnables:
            process_chain = process_chain | runnable

        # 解析链
        parse_chain = process_chain | RunnableLambda(
            custom_parser or default_parse_to_pydantic)

        # 重试链
        retry_chain = parse_chain.with_retry(
            retry_if_exception_type=(ValidationError, ValueError),
            stop_after_attempt=max_retries,
            wait_exponential_jitter=True,
            exponential_jitter_params={
                "initial": 0.1, "max": 3.0, "exp_base": 2.0, "jitter": 1.0}
        )

        return StructuredRunnableWithToken(retry_chain, self.langfuse)

    # ========== 实现BaseChatModel抽象方法 ==========
    def _generate(self, messages, stop=None, run_manager=None, ** kwargs):
        return self.llm._generate(messages, stop=stop, run_manager=run_manager, ** kwargs)

    @property
    def _llm_type(self) -> str:
        return self.llm._llm_type
