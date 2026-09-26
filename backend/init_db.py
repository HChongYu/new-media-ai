"""
数据库初始化脚本

用法：
    python init_db.py

功能：
    1. 创建所有数据表
    2. 创建默认管理员账号（admin / admin123）
"""
from app.database import engine, Base, SessionLocal
from app.models import (
    User,
    Topic,
    Content,
    Image,
    PublishRecord,
    Settings,
    ContentProject,
    PromptTemplate,
)
from app.core.security import hash_password
from app.graph.prompts import PROMPT_REGISTRY


def seed_prompt_templates(db) -> None:
    """将代码内置提示词作为 v1 种子写入（按 key 幂等，已有版本不动）"""
    for key, meta in PROMPT_REGISTRY.items():
        exists = db.query(PromptTemplate).filter(PromptTemplate.key == key).first()
        if exists:
            continue
        db.add(
            PromptTemplate(
                key=key,
                version=1,
                name=meta["name"],
                content=meta["template"],
                change_note="系统内置初始版本",
                status="active",
                variant="main",
            )
        )
    db.commit()
    print("提示词模板种子检查完成")


def init_database():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成")

    # 创建默认管理员 + 初始化提示词模板
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("默认管理员账号创建完成：admin / admin123")
        else:
            print("管理员账号已存在，跳过创建")

        seed_prompt_templates(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
