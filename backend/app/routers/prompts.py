"""
提示词工程化管理 API

- 版本管理：每个 key 的提示词以版本链形式存储，支持新建草稿、发布、回滚；
- 运行时修改：发布后节点立即读到新版本（prompt_service 缓存主动失效）；
- A/B 测试：可指定主干版本 + 1~2 个实验变体及流量百分比，
  运行时按 thread_id 哈希确定性分桶；
- 全程仅需登录（与 /settings 一致；RBAC 落地后可再加 admin 角色校验）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.prompt_template import PromptTemplate
from app.graph.prompts import PROMPT_REGISTRY
from app.schemas.common import ResponseModel
from app.schemas.prompt import (
    PromptVersionCreate,
    PromptVersionResponse,
    PromptKeySummaryResponse,
    ExperimentStartRequest,
)
from app.services.prompt_service import invalidate_cache

router = APIRouter()

_EXPERIMENT_VARIANT_NAMES = ("B", "C")


def _to_out(row: PromptTemplate) -> PromptVersionResponse:
    return PromptVersionResponse(
        id=row.id,
        key=row.key,
        version=row.version,
        name=row.name,
        content=row.content,
        change_note=row.change_note,
        status=row.status,
        variant=row.variant,
        traffic_percent=row.traffic_percent,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
    )


def _ensure_key(key: str) -> str:
    if key not in PROMPT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"未知的提示词 key：{key}")
    return key


def _get_version_or_404(db: Session, key: str, version: int) -> PromptTemplate:
    row = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.key == key, PromptTemplate.version == version)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"提示词 {key} 不存在版本 v{version}")
    return row


def _archive_all(db: Session, key: str) -> None:
    """归档 key 下全部版本，并重置实验字段"""
    rows = db.query(PromptTemplate).filter(PromptTemplate.key == key).all()
    for row in rows:
        row.status = "archived"
        row.variant = "main"
        row.traffic_percent = None


@router.get("", response_model=ResponseModel[list[PromptKeySummaryResponse]])
def list_prompt_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提示词键总览：内置 key、最新版本号、当前生效版本与实验状态"""
    result = []
    for key, meta in PROMPT_REGISTRY.items():
        all_rows = (
            db.query(PromptTemplate)
            .filter(PromptTemplate.key == key)
            .order_by(PromptTemplate.version.desc())
            .all()
        )
        active_rows = [row for row in all_rows if row.status == "active"]
        result.append(
            PromptKeySummaryResponse(
                key=key,
                name=meta["name"],
                latest_version=all_rows[0].version if all_rows else None,
                in_experiment=any(row.variant != "main" for row in active_rows),
                active=[_to_out(row) for row in active_rows],
            )
        )
    return ResponseModel(data=result)


@router.get("/{key}/versions", response_model=ResponseModel[list[PromptVersionResponse]])
def list_versions(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询某提示词的全部历史版本（新版本在前）"""
    _ensure_key(key)
    rows = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.key == key)
        .order_by(PromptTemplate.version.desc())
        .all()
    )
    return ResponseModel(data=[_to_out(row) for row in rows])


@router.post("/{key}/versions", response_model=ResponseModel[PromptVersionResponse])
def create_version(
    key: str,
    request: PromptVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """基于最新（或指定）版本创建新草稿，不影响线上生效版本"""
    _ensure_key(key)

    if request.base_version is not None:
        _get_version_or_404(db, key, request.base_version)

    latest = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.key == key)
        .order_by(PromptTemplate.version.desc())
        .first()
    )
    new_version = (latest.version + 1) if latest else 1

    row = PromptTemplate(
        key=key,
        version=new_version,
        name=PROMPT_REGISTRY[key]["name"],
        content=request.content,
        change_note=request.change_note,
        status="draft",
        variant="main",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ResponseModel(data=_to_out(row))


@router.post(
    "/{key}/versions/{version}/activate",
    response_model=ResponseModel[PromptVersionResponse],
)
def activate_version(
    key: str,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布指定版本（等价于把该版本切成唯一主干；对旧版本操作即「回滚」）"""
    _ensure_key(key)
    row = _get_version_or_404(db, key, version)

    _archive_all(db, key)
    row.status = "active"
    row.variant = "main"
    row.traffic_percent = None

    db.commit()
    db.refresh(row)
    invalidate_cache(key)
    return ResponseModel(data=_to_out(row))


@router.post("/{key}/experiment", response_model=ResponseModel[list[PromptVersionResponse]])
def start_experiment(
    key: str,
    request: ExperimentStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发起 A/B 实验：主干 main + 实验变体 B/C，按流量百分比哈希分桶"""
    _ensure_key(key)

    total_traffic = sum(item.traffic_percent for item in request.variants)
    if total_traffic > 100:
        raise HTTPException(status_code=400, detail="实验变体流量之和不能超过 100")

    versions = [item.version for item in request.variants]
    if len(set(versions)) != len(versions):
        raise HTTPException(status_code=400, detail="实验变体版本号不能重复")

    # 确定主干版本：显式指定 > 当前主干 > 最新版本
    baseline_row = None
    if request.baseline_version is not None:
        baseline_row = _get_version_or_404(db, key, request.baseline_version)
    else:
        baseline_row = (
            db.query(PromptTemplate)
            .filter(
                PromptTemplate.key == key,
                PromptTemplate.status == "active",
                PromptTemplate.variant == "main",
            )
            .order_by(PromptTemplate.version.desc())
            .first()
        )
        if baseline_row is None:
            baseline_row = (
                db.query(PromptTemplate)
                .filter(PromptTemplate.key == key)
                .order_by(PromptTemplate.version.desc())
                .first()
            )
    if baseline_row is None:
        raise HTTPException(status_code=400, detail="该提示词尚无任何版本，无法发起实验")

    if baseline_row.version in versions:
        raise HTTPException(status_code=400, detail="实验变体不能与主干版本相同")

    variant_rows = [_get_version_or_404(db, key, ver) for ver in versions]

    _archive_all(db, key)
    baseline_row.status = "active"
    baseline_row.variant = "main"
    baseline_row.traffic_percent = None

    activated = [baseline_row]
    for item, row, name in zip(request.variants, variant_rows, _EXPERIMENT_VARIANT_NAMES):
        row.status = "active"
        row.variant = name
        row.traffic_percent = item.traffic_percent
        activated.append(row)

    db.commit()
    for row in activated:
        db.refresh(row)
    invalidate_cache(key)
    return ResponseModel(data=[_to_out(row) for row in activated])


@router.delete("/{key}/experiment", response_model=ResponseModel[PromptVersionResponse])
def stop_experiment(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """停止 A/B 实验：归档实验变体，全部流量回归主干"""
    _ensure_key(key)

    main_row = (
        db.query(PromptTemplate)
        .filter(
            PromptTemplate.key == key,
            PromptTemplate.status == "active",
            PromptTemplate.variant == "main",
        )
        .first()
    )
    if main_row is None:
        raise HTTPException(status_code=400, detail="当前没有进行中的实验（无主干版本）")

    experiment_rows = (
        db.query(PromptTemplate)
        .filter(
            PromptTemplate.key == key,
            PromptTemplate.status == "active",
            PromptTemplate.variant != "main",
        )
        .all()
    )
    for row in experiment_rows:
        row.status = "archived"
        row.variant = "main"
        row.traffic_percent = None

    db.commit()
    db.refresh(main_row)
    invalidate_cache(key)
    return ResponseModel(data=_to_out(main_row))
