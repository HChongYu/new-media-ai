"""
Graph 组装、编译与全局持有

节点与边：
    START -> plan_topics -> human_select[interrupt]
          -> generate_draft -> human_review[interrupt]
          -> (approve: extract_visual_points -> generate_images -> END)
             (reject:  generate_draft 回环重写)
"""
from langgraph.graph import StateGraph, START, END

from app.graph.state import ArticleState
from app.graph.edges import route_after_review
from app.graph.nodes.planner import plan_topics
from app.graph.nodes.human import human_select, human_review
from app.graph.nodes.writer import generate_draft
from app.graph.nodes.visualizer import extract_visual_points, generate_images
from app.graph.checkpointer import checkpointer_lifecycle

# 节点名常量（也用于 next_step 与日志）
NODE_PLAN_TOPICS = "plan_topics"
NODE_HUMAN_SELECT = "human_select"
NODE_GENERATE_DRAFT = "generate_draft"
NODE_HUMAN_REVIEW = "human_review"
NODE_EXTRACT_VISUAL = "extract_visual_points"
NODE_GENERATE_IMAGES = "generate_images"


def build_article_graph(checkpointer=None):
    """组装并编译统一图文工作流"""
    graph = StateGraph(ArticleState)

    graph.add_node(NODE_PLAN_TOPICS, plan_topics)
    graph.add_node(NODE_HUMAN_SELECT, human_select)
    graph.add_node(NODE_GENERATE_DRAFT, generate_draft)
    graph.add_node(NODE_HUMAN_REVIEW, human_review)
    graph.add_node(NODE_EXTRACT_VISUAL, extract_visual_points)
    graph.add_node(NODE_GENERATE_IMAGES, generate_images)

    graph.add_edge(START, NODE_PLAN_TOPICS)
    graph.add_edge(NODE_PLAN_TOPICS, NODE_HUMAN_SELECT)
    graph.add_edge(NODE_HUMAN_SELECT, NODE_GENERATE_DRAFT)
    graph.add_edge(NODE_GENERATE_DRAFT, NODE_HUMAN_REVIEW)

    # 人工审核后的条件分支
    graph.add_conditional_edges(
        NODE_HUMAN_REVIEW,
        route_after_review,
        {
            "approve": NODE_EXTRACT_VISUAL,
            "reject": NODE_GENERATE_DRAFT,
        },
    )

    graph.add_edge(NODE_EXTRACT_VISUAL, NODE_GENERATE_IMAGES)
    graph.add_edge(NODE_GENERATE_IMAGES, END)

    return graph.compile(checkpointer=checkpointer)


# 编译后的全局图实例
_workflow = None


def get_workflow():
    """获取已编译的工作流（需先在 lifespan 中执行 init_workflow）"""
    if _workflow is None:
        raise RuntimeError("工作流尚未初始化，请先等待应用启动完成")
    return _workflow


async def init_workflow() -> None:
    """应用启动：初始化 checkpointer 并编译图"""
    global _workflow
    await checkpointer_lifecycle.startup()
    _workflow = build_article_graph(checkpointer_lifecycle.saver)


async def shutdown_workflow() -> None:
    """应用关闭：释放 checkpointer 连接"""
    global _workflow
    _workflow = None
    await checkpointer_lifecycle.shutdown()
