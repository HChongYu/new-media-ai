"""提示词管理接口 Schema"""
from pydantic import BaseModel, Field


class PromptVersionCreate(BaseModel):
    """新建新版本（草稿状态）"""

    content: str = Field(min_length=1, description="提示词正文（含 {占位符}）")
    change_note: str | None = Field(default=None, max_length=255, description="版本说明")
    base_version: int | None = Field(
        default=None, description="基于哪个已有版本创建；默认最新版本（仅用于预填校验）"
    )


class PromptVersionResponse(BaseModel):
    id: int
    key: str
    version: int
    name: str
    # content 默认在「版本列表」场景也返回（编辑器需要预填），大文本场景可后续按需拆分
    content: str
    change_note: str | None = None
    status: str
    variant: str
    traffic_percent: int | None = None
    created_at: str
    updated_at: str


class PromptKeySummaryResponse(BaseModel):
    """提示词键总览"""

    key: str
    name: str
    latest_version: int | None = None
    in_experiment: bool
    active: list[PromptVersionResponse]


class ExperimentVariantIn(BaseModel):
    """A/B 实验中的一个实验组（相对主干 main 的流量百分比）"""

    version: int = Field(description="参与实验的版本号")
    traffic_percent: int = Field(ge=1, le=100, description="该变体承接的流量百分比")


class ExperimentStartRequest(BaseModel):
    """发起 A/B 实验

    - baseline_version：主干版本，吃掉实验变体之外的剩余流量；
      不传则使用当前主干（无主干时取最新版本）
    - variants：实验变体 1-2 个（自动命名 B / C），流量之和 <= 100
    """

    baseline_version: int | None = None
    variants: list[ExperimentVariantIn] = Field(min_length=1, max_length=2)
