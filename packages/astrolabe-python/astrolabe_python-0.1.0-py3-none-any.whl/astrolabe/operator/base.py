from abc import ABC
from typing import Any, Dict, Optional

class Op(ABC):
    """
    算子基类

    所有算子都继承此类。算子是 Pipeline 的基本构建块，
    描述一个数据转换操作。

    设计原则：
    1. 声明式：算子只描述"做什么"，不描述"怎么做"
    2. 惰性执行：创建算子时不执行，由 Runner 负责执行
    3. 可组合：通过 Pipeline 串联多个算子

    Attributes:
        name: 算子名称，用于标识和日志
    """

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（子类可覆盖扩展）"""
        return {
            "type": self.__class__.__name__,
            "name": self.name,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
