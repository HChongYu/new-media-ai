"""
启动脚本

用法：
    python run.py
    # 或
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # 日志统一由 app.core.logging.setup_logging() 配置，禁止 uvicorn 覆盖
        log_config=None,
    )
