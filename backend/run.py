"""
开发启动入口：用命令行参数控制数据来源，无需修改 .env 文件。

用法（在 backend/ 目录下）：
    python run.py              # 真实模式：按 .env 配置调用真实 AI 服务
    python run.py --mock       # Mock 模式：全离线，LLM/图片走假数据、Checkpointer 用内存
    python run.py --mock --port 8001

说明：--mock 的本质是在配置加载前注入环境变量；
pydantic-settings 中环境变量优先级高于 .env，因此只影响本次启动。
"""
import argparse
import os
import socket
import sys

import uvicorn


def _enable_mock() -> None:
    """注入 mock 相关环境变量（不覆盖已显式设置的值）"""
    os.environ.setdefault("LLM_PROVIDER", "mock")
    os.environ.setdefault("IMAGE_PROVIDER", "mock")
    os.environ.setdefault("CHECKPOINTER_BACKEND", "memory")


def _ensure_port_free(host: str, port: int) -> None:
    """启动前检查端口，避免新实例静默失败、请求仍打到旧实例上"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        if probe.connect_ex((host, port)) == 0:
            print(
                f"[run] 端口 {port} 已被占用，可能已有一个后端在运行。\n"
                "      请先关闭旧进程（原终端按 Ctrl+C），或用 --port 指定其他端口。",
                file=sys.stderr,
            )
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI 自媒体运营平台 - 后端启动器")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="使用全离线 mock 数据（不请求真实 LLM / 生图，Checkpointer 用内存）",
    )
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="关闭代码变更自动重载（默认开启，便于开发）",
    )
    args = parser.parse_args()

    _ensure_port_free(args.host, args.port)

    if args.mock:
        _enable_mock()
        print("[run] 已启用 Mock 模式：LLM/图片使用假数据，Checkpointer 使用内存")
    else:
        print("[run] 真实模式：使用 .env 中的真实配置")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )


if __name__ == "__main__":
    main()
