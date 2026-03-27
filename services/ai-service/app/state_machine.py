from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any


class ConversationState(Enum):
    """对话状态枚举"""
    IDLE = auto()                    # 空闲状态
    EXTRACTING_ORIGIN = auto()       # 提取出发地
    EXTRACTING_DEST = auto()         # 提取目的地
    EXTRACTING_WEIGHT = auto()       # 提取重量
    CONFIRMING_COURIER = auto()      # 确认快递员
    QUOTED = auto()                  # 已报价
    LOCKED = auto()                  # 已锁定（等待支付）


@dataclass
class ConversationContext:
    """对话上下文数据类"""
    user_id: str
    current_state: ConversationState = ConversationState.IDLE
    extracted_info: dict[str, Any] = field(default_factory=dict)
    pending_confirmations: list[dict[str, Any]] = field(default_factory=list)
    session_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典，用于序列化"""
        return {
            "user_id": self.user_id,
            "current_state": self.current_state.name,
            "extracted_info": self.extracted_info,
            "pending_confirmations": self.pending_confirmations,
            "session_history": self.session_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationContext":
        """从字典创建实例"""
        return cls(
            user_id=data["user_id"],
            current_state=ConversationState[data["current_state"]],
            extracted_info=data.get("extracted_info", {}),
            pending_confirmations=data.get("pending_confirmations", []),
            session_history=data.get("session_history", []),
        )

    def update_state(self, new_state: ConversationState) -> None:
        """更新对话状态"""
        self.current_state = new_state

    def add_extracted_info(self, key: str, value: Any) -> None:
        """添加提取的信息"""
        self.extracted_info[key] = value

    def add_pending_confirmation(self, item: dict[str, Any]) -> None:
        """添加待确认项"""
        self.pending_confirmations.append(item)

    def clear_pending_confirmations(self) -> None:
        """清空待确认项"""
        self.pending_confirmations.clear()

    def add_to_history(self, message: dict[str, Any]) -> None:
        """添加消息到会话历史"""
        self.session_history.append(message)
        # 限制历史长度，保留最近 50 条
        if len(self.session_history) > 50:
            self.session_history = self.session_history[-50:]
