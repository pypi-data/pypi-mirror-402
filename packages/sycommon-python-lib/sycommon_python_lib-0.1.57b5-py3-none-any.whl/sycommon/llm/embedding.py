import asyncio
import aiohttp
import atexit
from typing import Union, List, Optional, Dict
from sycommon.config.Config import SingletonMeta
from sycommon.config.EmbeddingConfig import EmbeddingConfig
from sycommon.config.RerankerConfig import RerankerConfig
from sycommon.logging.kafka_log import SYLogger


class Embedding(metaclass=SingletonMeta):
    def __init__(self):
        # 1. 并发限制
        self.max_concurrency = 20
        # 保留默认模型名称
        self.default_embedding_model = "bge-large-zh-v1.5"
        self.default_reranker_model = "bge-reranker-large"

        # 初始化默认模型的基础URL
        self.embeddings_base_url = EmbeddingConfig.from_config(
            self.default_embedding_model).baseUrl
        self.reranker_base_url = RerankerConfig.from_config(
            self.default_reranker_model).baseUrl

        # [修复] 缓存配置URL，避免高并发下重复读取配置文件
        self._embedding_url_cache: Dict[str, str] = {
            self.default_embedding_model: self.embeddings_base_url
        }
        self._reranker_url_cache: Dict[str, str] = {
            self.default_reranker_model: self.reranker_base_url
        }

        # 并发信号量
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.default_timeout = aiohttp.ClientTimeout(total=None)

        # 核心优化：创建全局可复用的ClientSession（连接池复用）
        self.session = None

        # [修复] 注册退出钩子，确保程序结束时关闭连接池
        atexit.register(self._sync_close_session)

    async def init_session(self):
        """初始化全局ClientSession（仅创建一次）"""
        if self.session is None or self.session.closed:
            # 配置连接池参数，适配高并发
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrency,  # 连接池最大连接数
                limit_per_host=self.max_concurrency,  # 每个域名的最大连接数
                ttl_dns_cache=300,  # DNS缓存时间
                enable_cleanup_closed=True  # 自动清理关闭的连接
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.default_timeout
            )

    async def close_session(self):
        """关闭全局Session（程序退出时调用）"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _sync_close_session(self):
        """同步关闭Session的封装，供atexit调用"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # [修复] 修正缩进，确保 create_task 的异常能被捕获
                try:
                    loop.create_task(self.close_session())
                except Exception:
                    pass
            else:
                try:
                    loop.run_until_complete(self.close_session())
                except Exception:
                    pass
        except Exception:
            # 捕获获取 loop 时的异常
            pass

    def _get_embedding_url(self, model: str) -> str:
        """获取Embedding URL（带缓存）"""
        if model not in self._embedding_url_cache:
            self._embedding_url_cache[model] = EmbeddingConfig.from_config(
                model).baseUrl
        return self._embedding_url_cache[model]

    def _get_reranker_url(self, model: str) -> str:
        """获取Reranker URL（带缓存）"""
        if model not in self._reranker_url_cache:
            self._reranker_url_cache[model] = RerankerConfig.from_config(
                model).baseUrl
        return self._reranker_url_cache[model]

    async def _get_embeddings_http_core(
        self,
        input: Union[str, List[str]],
        encoding_format: str = None,
        model: str = None,
        timeout: aiohttp.ClientTimeout = None,
        **kwargs
    ):
        """embedding请求核心逻辑"""
        await self.init_session()  # 确保Session已初始化
        async with self.semaphore:
            request_timeout = timeout or self.default_timeout
            target_model = model or self.default_embedding_model

            # [修复] 使用缓存获取URL
            target_base_url = self._get_embedding_url(target_model)
            url = f"{target_base_url}/v1/embeddings"

            request_body = {
                "model": target_model,
                "input": input,
                "encoding_format": encoding_format or "float"
            }
            request_body.update(kwargs)

            # 复用全局Session
            try:
                async with self.session.post(
                    url,
                    json=request_body,
                    timeout=request_timeout
                ) as response:
                    if response.status != 200:
                        error_detail = await response.text()
                        # [日志] 记录详细的HTTP错误响应
                        SYLogger.error(
                            f"Embedding request HTTP Error. Status: {response.status}, "
                            f"Model: {target_model}, URL: {url}. Detail: {error_detail}"
                        )
                        return None
                    return await response.json()
            except (aiohttp.ClientConnectionResetError, asyncio.TimeoutError, aiohttp.ClientError) as e:
                # [日志] 记录网络错误
                SYLogger.error(
                    f"Embedding request Network Error. Model: {target_model}, URL: {url}. "
                    f"Error: {e.__class__.__name__} - {str(e)}"
                )
                return None
            except Exception as e:
                # 记录其他未预期的异常
                SYLogger.error(
                    f"Unexpected error in _get_embeddings_http_core: {str(e)}", exc_info=True)
                return None

    async def _get_embeddings_http_async(
        self,
        input: Union[str, List[str]],
        encoding_format: str = None,
        model: str = None,
        timeout: aiohttp.ClientTimeout = None, ** kwargs
    ):
        """对外暴露的embedding请求方法"""
        return await self._get_embeddings_http_core(
            input, encoding_format, model, timeout, ** kwargs
        )

    async def _get_reranker_http_core(
        self,
        documents: List[str],
        query: str,
        top_n: Optional[int] = None,
        model: str = None,
        max_chunks_per_doc: Optional[int] = None,
        return_documents: Optional[bool] = True,
        return_len: Optional[bool] = True,
        timeout: aiohttp.ClientTimeout = None, ** kwargs
    ):
        """reranker请求核心逻辑"""
        await self.init_session()  # 确保Session已初始化
        async with self.semaphore:
            request_timeout = timeout or self.default_timeout
            target_model = model or self.default_reranker_model

            # [修复] 使用缓存获取URL
            target_base_url = self._get_reranker_url(target_model)
            url = f"{target_base_url}/v1/rerank"

            request_body = {
                "model": target_model,
                "documents": documents,
                "query": query,
                "top_n": top_n or len(documents),
                "max_chunks_per_doc": max_chunks_per_doc,
                "return_documents": return_documents,
                "return_len": return_len,
            }
            request_body.update(kwargs)

            # 复用全局Session
            try:
                async with self.session.post(
                    url,
                    json=request_body,
                    timeout=request_timeout
                ) as response:
                    if response.status != 200:
                        error_detail = await response.text()
                        # [日志] 记录详细的HTTP错误响应
                        SYLogger.error(
                            f"Reranker request HTTP Error. Status: {response.status}, "
                            f"Model: {target_model}, URL: {url}. Detail: {error_detail}"
                        )
                        return None
                    return await response.json()
            except (aiohttp.ClientConnectionResetError, asyncio.TimeoutError, aiohttp.ClientError) as e:
                # [日志] 记录网络错误
                SYLogger.error(
                    f"Reranker request Network Error. Model: {target_model}, URL: {url}. "
                    f"Error: {e.__class__.__name__} - {str(e)}"
                )
                return None
            except Exception as e:
                # 记录其他未预期的异常
                SYLogger.error(
                    f"Unexpected error in _get_reranker_http_core: {str(e)}", exc_info=True)
                return None

    async def _get_reranker_http_async(
        self,
        documents: List[str],
        query: str,
        top_n: Optional[int] = None,
        model: str = None,
        max_chunks_per_doc: Optional[int] = None,
        return_documents: Optional[bool] = True,
        return_len: Optional[bool] = True,
        timeout: aiohttp.ClientTimeout = None, ** kwargs
    ):
        """对外暴露的reranker请求方法"""
        return await self._get_reranker_http_core(
            documents, query, top_n, model, max_chunks_per_doc,
            return_documents, return_len, timeout, **kwargs
        )

    def _get_dimension(self, model: str) -> int:
        """获取模型维度，用于生成兜底零向量"""
        try:
            config = EmbeddingConfig.from_config(model)
            if hasattr(config, 'dimension'):
                return int(config.dimension)
        except Exception:
            pass
        # 默认兜底 1024
        return 1024

    async def get_embeddings(
        self,
        corpus: List[str],
        model: str = None,
        timeout: Optional[Union[int, float]] = None
    ):
        """
        获取语料库的嵌入向量，结果顺序与输入语料库顺序一致

        Args:
            corpus: 待生成嵌入向量的文本列表
            model: 可选，指定使用的embedding模型名称，默认使用bge-large-zh-v1.5
            timeout: 可选，超时时间（秒）：
                     - 传int/float：表示总超时时间（秒）
                     - 不传/None：使用默认永不超时配置
        """
        request_timeout = None
        if timeout is not None:
            if isinstance(timeout, (int, float)):
                request_timeout = aiohttp.ClientTimeout(total=timeout)
            else:
                SYLogger.warning(
                    f"Invalid timeout type: {type(timeout)}, must be int/float, use default timeout")

        actual_model = model or self.default_embedding_model

        SYLogger.info(
            f"Requesting embeddings for corpus: {len(corpus)} items (model: {actual_model}, max_concurrency: {self.max_concurrency}, timeout: {timeout or 'None'})")

        all_vectors = []

        # [修复] 增加 Chunk 处理逻辑，防止 corpus 过大导致内存溢出或协程过多
        # 每次最多处理 max_concurrency * 2 个请求，避免一次性创建几十万个协程
        batch_size = self.max_concurrency * 2

        for i in range(0, len(corpus), batch_size):
            batch_texts = corpus[i: i + batch_size]

            # 给每个异步任务传入模型名称和超时配置
            tasks = [self._get_embeddings_http_async(
                text, model=model, timeout=request_timeout) for text in batch_texts]
            results = await asyncio.gather(*tasks)

            for result in results:
                if result is None:
                    dim = self._get_dimension(actual_model)

                    zero_vector = [0.0] * dim
                    all_vectors.append(zero_vector)
                    # [日志] 补充日志，明确是补零操作
                    SYLogger.warning(
                        f"Embedding request failed (returned None), appending zero vector ({dim}D) for model {actual_model}")
                    continue

                # 从返回结果中提取向量
                try:
                    for item in result["data"]:
                        embedding = item["embedding"]
                        all_vectors.append(embedding)
                except (KeyError, TypeError) as e:
                    SYLogger.error(f"Failed to parse embedding result: {e}")
                    dim = self._get_dimension(actual_model)
                    all_vectors.append([0.0] * dim)

        SYLogger.info(
            f"Embeddings for corpus created: {len(all_vectors)} vectors (model: {actual_model})")
        return all_vectors

    async def get_reranker(
        self,
        top_results: List[str],
        query: str,
        model: str = None,
        timeout: Optional[Union[int, float]] = None
    ):
        """
        对搜索结果进行重排序

        Args:
            top_results: 待重排序的文本列表
            query: 排序参考的查询语句
            model: 可选，指定使用的reranker模型名称，默认使用bge-reranker-large
            timeout: 可选，超时时间（秒）：
                     - 传int/float：表示总超时时间（秒）
                     - 不传/None：使用默认永不超时配置
        """
        request_timeout = None
        if timeout is not None:
            if isinstance(timeout, (int, float)):
                request_timeout = aiohttp.ClientTimeout(total=timeout)
            else:
                SYLogger.warning(
                    f"Invalid timeout type: {type(timeout)}, must be int/float, use default timeout")

        actual_model = model or self.default_reranker_model
        SYLogger.info(
            f"Requesting reranker for top_results: {top_results} (model: {actual_model}, max_concurrency: {self.max_concurrency}, timeout: {timeout or 'None'})")

        data = await self._get_reranker_http_async(
            top_results, query, model=model, timeout=request_timeout)
        SYLogger.info(
            f"Reranker for top_results completed (model: {actual_model})")
        return data
