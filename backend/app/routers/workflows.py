"""
统一图文工作流 API

交互流程（通过 thread_id 串联两次人工中断）：
    POST /api/workflows/start                 发起任务 -> 停在 human_select
    POST /api/workflows/{thread_id}/resume    人工选题 / 人工审稿恢复执行
    GET  /api/workflows/{thread_id}           查询当前状态
    GET  /api/workflows                       项目列表
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.core.logging import bind_thread_id, reset_context
from app.models.user import User
from app.models.workflow_project import ContentProject
from app.schemas.common import ResponseModel
from app.schemas.workflow import (
    WorkflowStartRequest,
    WorkflowResumeRequest,
    WorkflowProjectResponse,
    WorkflowRunResponse,
)
from app.graph.runner import (
    start_workflow,
    resume_workflow,
    get_snapshot,
    WorkflowSnapshot,
    expected_action,
)
from app.graph.state import INTERRUPT_SELECT, INTERRUPT_REVIEW

router = APIRouter()
logger = logging.getLogger(__name__)

# 中断点 -> 业务状态
_STATUS_BY_STEP = {
    INTERRUPT_SELECT: "awaiting_select",
    INTERRUPT_REVIEW: "reviewing",
}


def _project_resp(project: ContentProject) -> WorkflowProjectResponse:
    return WorkflowProjectResponse(
        id=project.id,
        thread_id=project.thread_id,
        topic_direction=project.topic_direction,
        topic=project.topic,
        platform=project.platform,
        status=project.status,
        revision_count=project.revision_count,
        article_content=project.article_content,
        image_assets=project.image_assets,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


def _sync_project(project: ContentProject, snap: WorkflowSnapshot) -> None:
    """
    将图状态同步到业务表（图本身不感知数据库，保持节点纯净）。

    注意：messages 等内部字段不外泄，只同步业务需要的字段。
    """
    values = snap.values
    if values.get("selected_topic"):
        project.topic = values["selected_topic"]
    if "revision_count" in values:
        project.revision_count = values["revision_count"]

    if snap.completed:
        project.status = "completed"
        project.article_content = {
            "title": values.get("draft_title", ""),
            "content": values.get("final_content", ""),
        }
        project.image_assets = list(values.get("image_urls", []))
    else:
        project.status = _STATUS_BY_STEP.get(snap.next_step, project.status)


def _run_resp(project: ContentProject, snap: WorkflowSnapshot) -> WorkflowRunResponse:
    values = snap.values
    return WorkflowRunResponse(
        project=_project_resp(project),
        next_step=snap.next_step,
        interrupt=snap.interrupt,
        completed=snap.completed,
        proposed_topics=values.get("proposed_topics", []),
        selected_topic=values.get("selected_topic", ""),
        draft_title=values.get("draft_title", ""),
        draft_content=values.get("draft_content", ""),
        final_content=values.get("final_content", ""),
        visual_points=values.get("visual_points", []),
        image_urls=values.get("image_urls", []),
        revision_count=values.get("revision_count", 0),
    )


async def _load_owned_project(
    thread_id: str, db: Session, user: User
) -> ContentProject:
    project = (
        db.query(ContentProject)
        .filter(ContentProject.thread_id == thread_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该工作流")
    return project


@router.post("/start", response_model=ResponseModel[WorkflowRunResponse])
async def start(
    request: WorkflowStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发起任务：生成备选选题后暂停，等待人工选择"""
    project = ContentProject(
        user_id=current_user.id,
        topic_direction=request.topic_direction,
        platform=request.platform,
        status="awaiting_select",
    )
    db.add(project)
    db.flush()  # 拿到 id / thread_id

    thread_token = bind_thread_id(project.thread_id)
    try:
        snap = await start_workflow(
            thread_id=project.thread_id,
            topic_direction=request.topic_direction,
            platform=request.platform,
        )
    except Exception as e:
        logger.error("启动工作流失败: %s", e, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"AI 工作流执行失败，请检查模型配置：{e}",
        )
    finally:
        reset_context(thread_token=thread_token)

    _sync_project(project, snap)
    db.commit()
    db.refresh(project)
    return ResponseModel(data=_run_resp(project, snap))


@router.post("/{thread_id}/resume", response_model=ResponseModel[WorkflowRunResponse])
async def resume(
    thread_id: str,
    request: WorkflowResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """人工介入后恢复：选题选择 / 草稿审核（通过或带意见驳回重写）"""
    project = await _load_owned_project(thread_id, db, current_user)

    snap = await get_snapshot(thread_id)
    if not snap.found:
        raise HTTPException(status_code=404, detail="工作流状态不存在或已丢失")
    if snap.completed:
        raise HTTPException(status_code=400, detail="工作流已完成，无需继续操作")

    want_action = expected_action(snap.next_step)
    if request.action != want_action:
        raise HTTPException(
            status_code=400,
            detail=f"当前中断点需要 {want_action} 操作，而不是 {request.action}",
        )

    # 构造 Command(resume=...) 的载荷
    if request.action == "select_topic":
        selected = (request.data or "").strip()
        if not selected:
            raise HTTPException(status_code=400, detail="缺少选中的选题 data")
        allowed = {t.get("title") for t in snap.values.get("proposed_topics", [])}
        if allowed and selected not in allowed:
            raise HTTPException(status_code=400, detail="选中的选题不在候选列表中")
        resume_value = selected
    else:  # review
        if request.status not in ("approve", "reject"):
            raise HTTPException(status_code=400, detail="审核状态必须是 approve 或 reject")
        if request.status == "reject" and not (request.feedback or "").strip():
            raise HTTPException(status_code=400, detail="驳回时必须填写修改意见 feedback")
        resume_value = {"status": request.status, "feedback": (request.feedback or "").strip()}

    thread_token = bind_thread_id(thread_id)
    try:
        new_snap = await resume_workflow(thread_id, resume_value)
    except Exception as e:
        logger.error("恢复工作流失败: %s", e, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"AI 工作流执行失败，请检查模型配置：{e}",
        )
    finally:
        reset_context(thread_token=thread_token)

    _sync_project(project, new_snap)
    db.commit()
    db.refresh(project)
    return ResponseModel(data=_run_resp(project, new_snap))


@router.get("/{thread_id}", response_model=ResponseModel[WorkflowRunResponse])
async def get_workflow_state(
    thread_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询工作流当前状态（不驱动执行）"""
    project = await _load_owned_project(thread_id, db, current_user)
    snap = await get_snapshot(thread_id)
    if not snap.found:
        # checkpointer 中无状态（如使用 MemorySaver 后重启），仅返回业务表数据
        return ResponseModel(
            data=_run_resp(
                project,
                WorkflowSnapshot(
                    thread_id=thread_id, next_step=None, interrupt=None, found=False
                ),
            )
        )
    _sync_project(project, snap)
    db.commit()
    return ResponseModel(data=_run_resp(project, snap))


@router.get("", response_model=ResponseModel[list[WorkflowProjectResponse]])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """工作流项目列表（用于历史归档页）"""
    query = db.query(ContentProject).filter(ContentProject.user_id == current_user.id)
    if status:
        query = query.filter(ContentProject.status == status)

    total = query.count()
    items = (
        query.order_by(ContentProject.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    logger.info("用户 %s 查询工作流列表，共 %d 条", current_user.id, total)
    return ResponseModel(data=[_project_resp(item) for item in items])
