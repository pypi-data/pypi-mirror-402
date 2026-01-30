#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AmazonMonitor 统一启动入口

运行模式（通过环境变量 RUN_MODE 配置）：
- web: 启动 uvicorn Web 服务（默认）
- cli: 启动命令行爬虫（支持终端进度显示）
- scheduler: 启动定时任务调度器（使用 cron 表达式）

两种模式只能选择其一，不能同时运行。
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


def load_env_config():
    """
    加载环境变量配置
    优先级：当前工作目录 .env > 用户主目录 .Amazon-monitor/.env > 系统环境变量
    """
    # 1. 当前工作目录
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)
        print(f"[配置] 已加载: {cwd_env}")
        return

    # 2. 用户主目录下的配置目录
    home_env = Path.home() / ".walmart-monitor" / ".env"
    if home_env.exists():
        load_dotenv(home_env, override=True)
        print(f"[配置] 已加载: {home_env}")
        return

    # 3. 没有找到 .env 文件，使用系统环境变量
    print("[配置] 未找到 .env 文件，使用系统环境变量")
    print(f"[提示] 可在以下位置创建 .env 文件:")
    print(f"       - {cwd_env}")
    print(f"       - {home_env}")


# 加载环境变量
load_env_config()

# 运行模式（在 load_env_config 之后读取）
RUN_MODE = os.getenv("RUN_MODE", "web").lower()
# Cron 表达式（仅 scheduler 模式使用）
CRON_EXPRESSION = os.getenv("CRON_EXPRESSION", "0 */2 * * *")  # 默认每2小时执行一次
# Web 服务配置
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))


def setup_logging():
    """配置日志"""
    log_dir = "data"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def run_web_server():
    """启动 uvicorn Web 服务"""
    import uvicorn
    logger = logging.getLogger(__name__)
    logger.info(f"启动 Web 服务模式: http://{WEB_HOST}:{WEB_PORT}")
    logger.info("终端进度显示已禁用，请使用 /task/progress API 查询任务进度")

    uvicorn.run(
        "app.main:app",
        host=WEB_HOST,
        port=WEB_PORT,
        reload=False,
        log_level="info"
    )


def run_cli_task():
    """运行单次 CLI 爬虫任务"""
    logger = logging.getLogger(__name__)
    logger.info("启动 CLI 模式（单次执行）")

    # 强制启用终端 UI
    os.environ["ENABLE_TERMINAL_UI"] = "true"

    from app.spider import run_task
    from app.main import get_urls_from_sources

    try:
        # 获取 URL 列表
        urls, data_source = get_urls_from_sources()
        logger.info(f"获取到 {len(urls)} 个 URL，数据来源: {data_source}")

        if not urls:
            logger.warning("没有获取到任何 URL，任务结束")
            return

        # 执行爬虫任务
        results = run_task(urls, data_source)
        logger.info(f"任务完成，共处理 {len(results)} 个 URL")

    except Exception as e:
        logger.error(f"CLI 任务执行失败: {e}", exc_info=True)
        sys.exit(1)


def run_scheduler():
    """启动定时任务调度器"""
    try:
        from croniter import croniter
    except ImportError:
        print("错误: 请先安装 croniter 库: pip install croniter")
        sys.exit(1)

    logger = logging.getLogger(__name__)
    logger.info(f"启动定时任务调度器模式")
    logger.info(f"Cron 表达式: {CRON_EXPRESSION}")

    # 强制启用终端 UI
    os.environ["ENABLE_TERMINAL_UI"] = "true"

    from app.spider import run_task
    from app.main import get_urls_from_sources
    from app.notifier import ding_talk_notifier

    # 信号处理
    running = True

    def signal_handler(signum, frame):
        nonlocal running
        logger.info("收到停止信号，正在退出...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 计算下次执行时间
    cron = croniter(CRON_EXPRESSION, datetime.now())

    def get_next_run_time():
        return cron.get_next(datetime)

    next_run = get_next_run_time()
    logger.info(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    while running:
        now = datetime.now()

        if now >= next_run:
            logger.info("=" * 50)
            logger.info(f"开始执行定时任务: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 50)

            try:
                # 获取 URL 列表
                urls, data_source = get_urls_from_sources()
                logger.info(f"获取到 {len(urls)} 个 URL，数据来源: {data_source}")

                if urls:
                    # 发送任务开始通知
                    title = "定时任务启动"
                    text = f"""### 定时任务启动

**启动时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}

**数据来源**: {data_source}

**商品数量**: {len(urls)} 个

**Cron 表达式**: {CRON_EXPRESSION}"""
                    ding_talk_notifier.send_markdown(title, text, is_at_all=False)

                    # 执行爬虫任务
                    results = run_task(urls, data_source)
                    logger.info(f"定时任务完成，共处理 {len(results)} 个 URL")
                else:
                    logger.warning("没有获取到任何 URL，跳过本次任务")

            except Exception as e:
                logger.error(f"定时任务执行失败: {e}", exc_info=True)
                # 发送错误通知
                try:
                    title = "定时任务执行失败"
                    text = f"""### 定时任务执行失败

**时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}

**错误**: {str(e)}"""
                    ding_talk_notifier.send_markdown(title, text, is_at_all=True)
                except Exception:
                    pass

            # 计算下次执行时间
            cron = croniter(CRON_EXPRESSION, datetime.now())
            next_run = get_next_run_time()
            logger.info(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        # 休眠 1 秒
        time.sleep(1)

    logger.info("定时任务调度器已停止")


def main():
    """主入口"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("AmazonMonitor 启动")
    logger.info(f"运行模式: {RUN_MODE}")
    logger.info("=" * 60)

    if RUN_MODE == "web":
        run_web_server()
    elif RUN_MODE == "cli":
        run_cli_task()
    elif RUN_MODE == "scheduler":
        run_scheduler()
    else:
        logger.error(f"未知的运行模式: {RUN_MODE}")
        logger.error("支持的模式: web, cli, scheduler")
        sys.exit(1)


if __name__ == "__main__":
    main()
