"""
MinerU KIE SDK

一个用于与 MinerU KIE 服务交互的 Python SDK。

主要功能：
- 文件上传
- 结果查询
- 文档解析、分割和提取
"""

from .kie import (
    MineruKIEClient,
    ParseResult,
    SplitResult,
    ExtractResult,
    StepResult,
)
from .common import guess_file_type

__version__ = "0.1.0"
__all__ = [
    "MineruKIEClient",
    "ParseResult",
    "SplitResult",
    "ExtractResult",
    "StepResult",
    "guess_file_type",
]
