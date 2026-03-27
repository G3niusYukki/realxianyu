import json
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timedelta, timezone
import redis.asyncio as redis
import asyncpg


@dataclass
class RequestContext:
    """L0: 单次请求上下文"""
    request_id: str
    user_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentState:
    """L1: 意图状态 (Redis, TTL 1h)"""
    user_id: str
    current_intent: str = ""
    intent_confidence: float = 0.0
    extracted_slots: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "current_intent": self.current_intent,
            "intent_confidence": self.intent_confidence,
            "extracted_slots": self.extracted_slots,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntentState":
        return cls(
            user_id=data["user_id"],
            current_intent=data.get("current_intent", ""),
            intent_confidence=data.get("intent_confidence", 0.0),
            extracted_slots=data.get("extracted_slots", {}),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class SessionMemory:
    """L2: 会话记忆 (Redis, TTL 24h)"""
    user_id: str
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMemory":
        return cls(
            user_id=data["user_id"],
            session_id=data["session_id"],
            messages=data.get("messages", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
        )


@dataclass
class UserProfile:
    """L3: 用户画像 (PostgreSQL)"""
    user_id: str
    preferred_couriers: list[str] = field(default_factory=list)
    common_routes: list[dict[str, Any]] = field(default_factory=list)
    price_sensitivity: str = "medium"  # low, medium, high
    communication_style: str = "casual"  # formal, casual, concise
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "preferred_couriers": self.preferred_couriers,
            "common_routes": self.common_routes,
            "price_sensitivity": self.price_sensitivity,
            "communication_style": self.communication_style,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ContextManager:
    """上下文管理器 - 管理 L0-L3 四级上下文"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        pg_dsn: str = "postgresql://localhost:5432/xianyuflow",
    ):
        self.redis_url = redis_url
        self.pg_dsn = pg_dsn
        self._redis: Optional[redis.Redis] = None
        self._pg_pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """初始化连接"""
        self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        self._pg_pool = await asyncpg.create_pool(self.pg_dsn)

    async def close(self) -> None:
        """关闭连接"""
        if self._redis:
            await self._redis.close()
        if self._pg_pool:
            await self._pg_pool.close()

    # L0: Request Context
    def create_request_context(
        self, request_id: str, user_id: str, metadata: Optional[dict[str, Any]] = None
    ) -> RequestContext:
        """创建请求上下文"""
        return RequestContext(
            request_id=request_id,
            user_id=user_id,
            metadata=metadata or {},
        )

    # L1: Intent State (Redis, TTL 1h)
    async def get_intent_state(self, user_id: str) -> Optional[IntentState]:
        """获取意图状态"""
        if not self._redis:
            raise RuntimeError("Redis not initialized")
        key = f"intent:{user_id}"
        data = await self._redis.get(key)
        if data:
            return IntentState.from_dict(json.loads(data))
        return None

    async def set_intent_state(self, state: IntentState, ttl: int = 3600) -> None:
        """设置意图状态，默认TTL 1小时"""
        if not self._redis:
            raise RuntimeError("Redis not initialized")
        key = f"intent:{state.user_id}"
        await self._redis.setex(key, ttl, json.dumps(state.to_dict()))

    async def delete_intent_state(self, user_id: str) -> None:
        """删除意图状态"""
        if not self._redis:
            raise RuntimeError("Redis not initialized")
        await self._redis.delete(f"intent:{user_id}")

    # L2: Session Memory (Redis, TTL 24h)
    async def get_session_memory(self, user_id: str, session_id: str) -> Optional[SessionMemory]:
        """获取会话记忆"""
        if not self._redis:
            raise RuntimeError("Redis not initialized")
        key = f"session:{user_id}:{session_id}"
        data = await self._redis.get(key)
        if data:
            return SessionMemory.from_dict(json.loads(data))
        return SessionMemory(user_id=user_id, session_id=session_id)

    async def set_session_memory(self, memory: SessionMemory, ttl: int = 86400) -> None:
        """设置会话记忆，默认TTL 24小时"""
        if not self._redis:
            raise RuntimeError("Redis not initialized")
        key = f"session:{memory.user_id}:{memory.session_id}"
        memory.last_active = datetime.now(timezone.utc)
        await self._redis.setex(key, ttl, json.dumps(memory.to_dict()))

    async def append_session_message(
        self, user_id: str, session_id: str, message: dict[str, Any]
    ) -> None:
        """追加会话消息"""
        memory = await self.get_session_memory(user_id, session_id)
        memory.messages.append(message)
        # 保留最近 100 条消息
        if len(memory.messages) > 100:
            memory.messages = memory.messages[-100:]
        await self.set_session_memory(memory)

    # L3: User Profile (PostgreSQL)
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        if not self._pg_pool:
            raise RuntimeError("PostgreSQL not initialized")
        async with self._pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1", user_id
            )
            if row:
                return UserProfile(
                    user_id=row["user_id"],
                    preferred_couriers=json.loads(row["preferred_couriers"]),
                    common_routes=json.loads(row["common_routes"]),
                    price_sensitivity=row["price_sensitivity"],
                    communication_style=row["communication_style"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            return None

    async def save_user_profile(self, profile: UserProfile) -> None:
        """保存用户画像"""
        if not self._pg_pool:
            raise RuntimeError("PostgreSQL not initialized")
        profile.updated_at = datetime.now(timezone.utc)
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_profiles (
                    user_id, preferred_couriers, common_routes,
                    price_sensitivity, communication_style, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO UPDATE SET
                    preferred_couriers = EXCLUDED.preferred_couriers,
                    common_routes = EXCLUDED.common_routes,
                    price_sensitivity = EXCLUDED.price_sensitivity,
                    communication_style = EXCLUDED.communication_style,
                    updated_at = EXCLUDED.updated_at
                """,
                profile.user_id,
                json.dumps(profile.preferred_couriers),
                json.dumps(profile.common_routes),
                profile.price_sensitivity,
                profile.communication_style,
                profile.created_at,
                profile.updated_at,
            )

    async def get_full_context(
        self, user_id: str, session_id: str, request_id: str
    ) -> dict[str, Any]:
        """获取完整上下文 (L0-L3)"""
        request_ctx = self.create_request_context(request_id, user_id)
        intent_state = await self.get_intent_state(user_id)
        session_memory = await self.get_session_memory(user_id, session_id)
        user_profile = await self.get_user_profile(user_id)

        return {
            "l0_request": request_ctx,
            "l1_intent": intent_state,
            "l2_session": session_memory,
            "l3_profile": user_profile,
        }
