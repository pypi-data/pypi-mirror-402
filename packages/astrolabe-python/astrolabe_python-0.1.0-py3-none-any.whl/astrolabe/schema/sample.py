"""Sample - 完整对话样本"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from .interaction import Interaction


class DataSource(str, Enum):
    """数据来源"""
    ONLINE_LOG = "online_log"
    HUMAN_LABEL = "human_label"
    SYNTHETIC = "synthetic"
    EXTERNAL = "external"


class Sample(BaseModel):
    """
    完整对话样本

    包含一个完整对话的所有交互记录，以及相关元信息。

    Attributes:
        sample_id: 样本唯一标识
        interactions: 交互记录列表

        # 血缘（数据溯源）
        source: 数据来源 (online_log / human_label / synthetic)
        request_id: 原始请求 ID
        model_name: 模型名称
        model_version: 模型版本

        # 切片 & 筛选
        scenario: 场景标签
        language: 语言
        tags: 标签列表

        # 生命周期
        created_at: 创建时间戳

        # 元数据
        metadata: 附加元数据
    """
    sample_id: str = Field(..., description="样本唯一标识")
    interactions: List[Interaction] = Field(default_factory=list, description="交互记录列表")

    # 血缘（数据溯源）
    source: str = Field(default="unknown", description="数据来源")
    request_id: Optional[str] = Field(default=None, description="原始请求 ID")
    model_name: Optional[str] = Field(default=None, description="模型名称")
    model_version: Optional[str] = Field(default=None, description="模型版本")

    # 切片 & 筛选
    scenario: Optional[str] = Field(default=None, description="场景标签")
    language: Optional[str] = Field(default=None, description="语言")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    # 生命周期
    created_at: int = Field(..., description="创建时间戳（毫秒）")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")

    def as_openai_format(self) -> List[Dict[str, Any]]:
        """转换为 OpenAI API 消息格式"""
        return [interaction.as_openai_format() for interaction in self.interactions]

    def as_gemini_format(self) -> Dict[str, Any]:
        """转换为 Gemini API 格式"""
        system_instruction = None
        contents = []

        for interaction in self.interactions:
            if interaction.role == "system":
                system_instruction = (
                    interaction.content
                    if isinstance(interaction.content, str)
                    else str(interaction.content)
                )
            else:
                contents.append(interaction.as_gemini_format())

        result = {"contents": contents}
        if system_instruction:
            result["system_instruction"] = {"parts": [{"text": system_instruction}]}

        return result

    def as_claude_format(self) -> Dict[str, Any]:
        """转换为 Claude API 格式"""
        system = None
        messages = []

        for interaction in self.interactions:
            if interaction.role == "system":
                system = (
                    interaction.content
                    if isinstance(interaction.content, str)
                    else str(interaction.content)
                )
            else:
                messages.append(interaction.as_claude_format())

        result = {"messages": messages}
        if system:
            result["system"] = system

        return result

    def get_user_turns(self) -> List[Interaction]:
        """获取所有用户轮次"""
        return [i for i in self.interactions if i.role == "user"]

    def get_assistant_turns(self) -> List[Interaction]:
        """获取所有助手轮次"""
        return [i for i in self.interactions if i.role == "assistant"]

    def turn_count(self) -> int:
        """获取对话轮数（一问一答算一轮）"""
        return len(self.get_user_turns())


def create_sample_from_messages(
    messages: List[Dict[str, Any]],
    sample_id: str,
    source: str = "synthetic",
    **kwargs
) -> Sample:
    """
    从 OpenAI 格式消息创建 Sample

    Args:
        messages: OpenAI 格式的消息列表
        sample_id: 样本 ID
        source: 数据来源
        **kwargs: 传递给 Sample 的其他参数

    Returns:
        Sample 对象
    """
    import time

    interactions = []
    for msg in messages:
        interaction = Interaction(
            type="message",
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
        )
        interactions.append(interaction)

    return Sample(
        sample_id=sample_id,
        interactions=interactions,
        source=source,
        created_at=kwargs.pop("created_at", int(time.time() * 1000)),
        **kwargs
    )
