"""
AI Service - FastAPI 应用入口
"""
import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.client import DeepSeekClient, ChatCompletionResponse, StreamChunk
from app.context import ContextManager
from app.state_machine import ConversationContext, ConversationState


# 全局客户端实例
llm_client: DeepSeekClient
context_manager: ContextManager


class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色: system, user, assistant")
    content: str = Field(..., description="消息内容")


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="对话消息列表")
    model: str = Field(default="deepseek-chat", description="模型名称")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int | None = Field(default=None, description="最大token数")
    stream: bool = Field(default=False, description="是否流式响应")
    user_id: str | None = Field(default=None, description="用户ID")
    session_id: str | None = Field(default=None, description="会话ID")


class ChatCompletionResponseModel(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int]


class ContextResponse(BaseModel):
    user_id: str
    l0_request: dict[str, Any] | None
    l1_intent: dict[str, Any] | None
    l2_session: dict[str, Any] | None
    l3_profile: dict[str, Any] | None


class StateUpdateRequest(BaseModel):
    new_state: str = Field(..., description="新状态名称")
    extracted_info: dict[str, Any] | None = Field(default=None, description="提取的信息")


class StateResponse(BaseModel):
    user_id: str
    current_state: str
    extracted_info: dict[str, Any]
    pending_confirmations: list[dict[str, Any]]
    session_history: list[dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global llm_client, context_manager

    # 初始化
    llm_client = DeepSeekClient(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    )
    context_manager = ContextManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        pg_dsn=os.getenv("DATABASE_URL", "postgresql://localhost:5432/xianyuflow"),
    )
    await context_manager.initialize()

    yield

    # 清理
    await llm_client.close()
    await context_manager.close()


app = FastAPI(
    title="AI Service",
    description="XianyuFlow AI Service - LLM调用和对话上下文管理",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查端点"""
    return {"status": "healthy", "service": "ai-service"}


@app.post("/api/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> Any:
    """
    聊天完成接口

    支持流式和非流式响应，自动管理上下文
    """
    try:
        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # 如果有用户ID，更新会话历史
        if request.user_id and request.session_id:
            # 添加用户消息到历史
            if messages and messages[-1]["role"] == "user":
                await context_manager.append_session_message(
                    request.user_id,
                    request.session_id,
                    {"role": "user", "content": messages[-1]["content"]},
                )

        # 调用 LLM
        response = await llm_client.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
        )

        if request.stream:
            # 流式响应
            async def stream_generator() -> AsyncIterator[str]:
                full_content = ""
                async for chunk in response:
                    if chunk.content:
                        full_content += chunk.content
                        data = json.dumps(
                            {
                                "choices": [
                                    {
                                        "delta": {"content": chunk.content},
                                        "finish_reason": None,
                                    }
                                ]
                            },
                            ensure_ascii=False,
                        )
                        yield f"data: {data}\n\n"
                    if chunk.finish_reason:
                        data = json.dumps(
                            {
                                "choices": [
                                    {
                                        "delta": {},
                                        "finish_reason": chunk.finish_reason,
                                    }
                                ]
                            },
                            ensure_ascii=False,
                        )
                        yield f"data: {data}\n\n"
                        yield "data: [DONE]\n\n"

                # 保存助手回复到历史
                if request.user_id and request.session_id and full_content:
                    await context_manager.append_session_message(
                        request.user_id,
                        request.session_id,
                        {"role": "assistant", "content": full_content},
                    )

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
            )
        else:
            # 非流式响应
            if isinstance(response, ChatCompletionResponse):
                # 保存助手回复到历史
                if request.user_id and request.session_id:
                    await context_manager.append_session_message(
                        request.user_id,
                        request.session_id,
                        {"role": "assistant", "content": response.content},
                    )

                return ChatCompletionResponseModel(
                    id=str(uuid.uuid4()),
                    created=int(__import__("time").time()),
                    model=response.model,
                    choices=[
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response.content,
                            },
                            "finish_reason": response.finish_reason or "stop",
                        }
                    ],
                    usage=response.usage,
                )
            else:
                raise HTTPException(status_code=500, detail="Unexpected response type")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@app.post("/api/v1/context/{user_id}", response_model=ContextResponse)
async def get_user_context(
    user_id: str,
    session_id: str | None = None,
    request_id: str | None = None,
) -> ContextResponse:
    """
    获取用户完整上下文 (L0-L3)
    """
    try:
        session_id = session_id or f"session_{user_id}"
        request_id = request_id or str(uuid.uuid4())

        full_context = await context_manager.get_full_context(
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
        )

        return ContextResponse(
            user_id=user_id,
            l0_request=full_context["l0_request"].__dict__ if full_context["l0_request"] else None,
            l1_intent=full_context["l1_intent"].to_dict() if full_context["l1_intent"] else None,
            l2_session=full_context["l2_session"].to_dict() if full_context["l2_session"] else None,
            l3_profile=full_context["l3_profile"].to_dict() if full_context["l3_profile"] else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@app.post("/api/v1/state/{user_id}", response_model=StateResponse)
async def update_conversation_state(
    user_id: str,
    request: StateUpdateRequest,
) -> StateResponse:
    """
    更新对话状态
    """
    try:
        # 获取或创建会话上下文
        session_id = f"state_{user_id}"

        # 从 Redis 获取现有状态（简化实现）
        # 实际项目中应该使用专门的 state 存储
        conv_context = ConversationContext(user_id=user_id)

        # 更新状态
        try:
            new_state = ConversationState[request.new_state]
            conv_context.update_state(new_state)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid state: {request.new_state}")

        # 更新提取的信息
        if request.extracted_info:
            for key, value in request.extracted_info.items():
                conv_context.add_extracted_info(key, value)

        return StateResponse(
            user_id=user_id,
            current_state=conv_context.current_state.name,
            extracted_info=conv_context.extracted_info,
            pending_confirmations=conv_context.pending_confirmations,
            session_history=conv_context.session_history,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update state: {str(e)}")


@app.get("/api/v1/state/{user_id}", response_model=StateResponse)
async def get_conversation_state(user_id: str) -> StateResponse:
    """
    获取当前对话状态
    """
    try:
        # 简化实现，实际应从存储中获取
        conv_context = ConversationContext(user_id=user_id)

        return StateResponse(
            user_id=user_id,
            current_state=conv_context.current_state.name,
            extracted_info=conv_context.extracted_info,
            pending_confirmations=conv_context.pending_confirmations,
            session_history=conv_context.session_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
