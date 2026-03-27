import os
import asyncio
from typing import AsyncIterator, Optional
import httpx
from dataclasses import dataclass


@dataclass
class ChatCompletionResponse:
    """聊天完成响应"""
    content: str
    model: str
    usage: dict[str, int]
    finish_reason: Optional[str] = None


@dataclass
class StreamChunk:
    """流式响应块"""
    content: str
    finish_reason: Optional[str] = None


class DeepSeekClient:
    """DeepSeek LLM 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.close()

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> ChatCompletionResponse | AsyncIterator[StreamChunk]:
        """
        发送聊天完成请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            stream: 是否使用流式响应

        Returns:
            如果 stream=False，返回 ChatCompletionResponse
            如果 stream=True，返回 AsyncIterator[StreamChunk]
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        if stream:
            return self._stream_chat_completion(url, payload)

        # 非流式请求，带重试
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                client = await self._get_client()
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                choice = data["choices"][0]
                return ChatCompletionResponse(
                    content=choice["message"]["content"],
                    model=data["model"],
                    usage=data.get("usage", {}),
                    finish_reason=choice.get("finish_reason"),
                )
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    # 可重试错误
                    wait_time = 2 ** attempt  # 指数退避
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_error = e
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
                continue

        raise last_error or RuntimeError("Max retries exceeded")

    async def _stream_chat_completion(
        self, url: str, payload: dict
    ) -> AsyncIterator[StreamChunk]:
        """流式聊天完成"""
        client = await self._get_client()

        async def stream_generator() -> AsyncIterator[StreamChunk]:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]  # 去掉 "data: " 前缀
                    if data == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        finish_reason = chunk["choices"][0].get("finish_reason")
                        content = delta.get("content", "")
                        if content or finish_reason:
                            yield StreamChunk(content=content, finish_reason=finish_reason)
                    except (json.JSONDecodeError, KeyError):
                        continue

        return stream_generator()

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 发送一个简单的请求检查 API 可用性
            response = await self.chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return isinstance(response, ChatCompletionResponse)
        except Exception:
            return False
