"""Interaction - 单次交互记录"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class InteractionType(str, Enum):
    """交互类型"""
    MESSAGE = "message"
    FUNCTION_CALL = "function_call"
    FUNCTION_CALL_OUTPUT = "function_call_output"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class Role(str, Enum):
    """角色类型"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Interaction(BaseModel):
    """
    单次交互记录

    表示对话中的一条消息、函数调用或其他交互。

    Attributes:
        type: 交互类型 (message / function_call / function_call_output / ...)
        role: 角色 (system / user / assistant / tool)
        content: 原始文本内容
        timestamp: 时间戳（毫秒）
        reward: 奖励值（用于 RLHF）
        quality_score: 质量评分
        function_name: 函数名称（当 type 为 function_call 时）
        function_args: 函数参数
        tool_call_id: 工具调用 ID
        metadata: 附加元数据
    """
    type: str = Field(default="message", description="交互类型")
    role: str = Field(..., description="角色: system/user/assistant/tool")
    content: Union[str, List[Any]] = Field(default="", description="原始文本或内容列表")
    timestamp: Optional[int] = Field(default=None, description="时间戳（毫秒）")

    # 评估 / 反馈
    reward: Optional[float] = Field(default=None, description="奖励值（RLHF）")
    quality_score: Optional[float] = Field(default=None, description="质量评分")

    # 函数调用相关
    function_name: Optional[str] = Field(default=None, description="函数名称")
    function_args: Optional[Dict[str, Any]] = Field(default=None, description="函数参数")
    tool_call_id: Optional[str] = Field(default=None, description="工具调用 ID")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")

    class Config:
        use_enum_values = True

    def as_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI API 格式"""
        msg = {"role": self.role}

        if self.type == "function_call" and self.function_name:
            msg["content"] = None
            msg["tool_calls"] = [{
                "id": self.tool_call_id or f"call_{id(self)}",
                "type": "function",
                "function": {
                    "name": self.function_name,
                    "arguments": (
                        self.function_args
                        if isinstance(self.function_args, str)
                        else str(self.function_args) if self.function_args else "{}"
                    ),
                }
            }]
        elif self.type == "function_call_output":
            msg["role"] = "tool"
            msg["content"] = self.content if isinstance(self.content, str) else str(self.content)
            msg["tool_call_id"] = self.tool_call_id or ""
        else:
            msg["content"] = self.content if isinstance(self.content, str) else str(self.content)

        return msg

    def as_gemini_format(self) -> Dict[str, Any]:
        """转换为 Gemini API 格式"""
        role_map = {"user": "user", "assistant": "model", "system": "user", "tool": "function"}
        role = role_map.get(self.role, "user")

        if self.type == "function_call" and self.function_name:
            return {
                "role": "model",
                "parts": [{
                    "functionCall": {
                        "name": self.function_name,
                        "args": self.function_args or {},
                    }
                }]
            }
        elif self.type == "function_call_output":
            return {
                "role": "function",
                "parts": [{
                    "functionResponse": {
                        "name": self.function_name or "unknown",
                        "response": {"result": self.content},
                    }
                }]
            }
        else:
            content = self.content if isinstance(self.content, str) else str(self.content)
            return {
                "role": role,
                "parts": [{"text": content}]
            }

    def as_claude_format(self) -> Dict[str, Any]:
        """转换为 Claude API 格式"""
        if self.type == "function_call" and self.function_name:
            return {
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "id": self.tool_call_id or f"toolu_{id(self)}",
                    "name": self.function_name,
                    "input": self.function_args or {},
                }]
            }
        elif self.type == "function_call_output":
            return {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": self.tool_call_id or "",
                    "content": self.content if isinstance(self.content, str) else str(self.content),
                }]
            }
        else:
            content = self.content if isinstance(self.content, str) else str(self.content)
            return {
                "role": self.role if self.role in ["user", "assistant"] else "user",
                "content": content,
            }
