import os
import random
import logging
from typing import List, Dict, TypedDict, Optional
from dotenv import load_dotenv

# 只在模块加载时调用一次
load_dotenv()


def setup_logging(log_file: str = "data/app.log") -> None:
    """
    统一配置日志系统。

    Args:
        log_file: 日志文件路径
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


# 模块级 logger
logger = logging.getLogger(__name__)


class Settings:
    """加载所有环境变量配置"""

    # 钉钉通知配置
    DINGTALK_WEBHOOK: str = os.getenv("DINGTALK_WEBHOOK", "")
    DINGTALK_SECRET: str = os.getenv("DINGTALK_SECRET", "")

    # Chrome 配置
    CHROME_USER_DATA_PATH: str = os.getenv("CHROME_USER_DATA_PATH", "")

    # 运行模式配置
    # RUN_MODE: web(默认) | cli | scheduler
    # - web: uvicorn Web 服务
    # - cli: 单次执行命令行爬虫（支持终端进度显示）
    # - scheduler: 定时任务调度器（使用 cron 表达式）
    RUN_MODE: str = os.getenv("RUN_MODE", "web")

    # 定时任务 cron 表达式（仅 scheduler 模式使用）
    # 默认每2小时执行一次
    CRON_EXPRESSION: str = os.getenv("CRON_EXPRESSION", "0 */2 * * *")

    # Web 服务配置
    WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))

    # 终端UI开关（仅 cli/scheduler 模式有效，web 模式自动禁用）
    ENABLE_TERMINAL_UI: bool = os.getenv("ENABLE_TERMINAL_UI", "true").lower() in ("true", "1")

    # 并发爬取配置
    # 并发标签页数量，默认3个
    SPIDER_CONCURRENCY: int = int(os.getenv("SPIDER_CONCURRENCY", "3"))

    # 第三轮浏览器重启重试最大次数，默认3次
    BROWSER_RESTART_MAX_RETRIES: int = int(os.getenv("BROWSER_RESTART_MAX_RETRIES", "3"))

    # 历史记录配置
    # 是否启用异常历史记录到钉钉表格
    HISTORY_RECORD_ENABLED: bool = os.getenv("HISTORY_RECORD_ENABLED", "true").lower() in ("true", "1")
    # 历史记录sheet名称
    HISTORY_SHEET_NAME: str = os.getenv("HISTORY_SHEET_NAME", "异常记录")

    # === 双平台监控配置 ===
    # 是否启用 Walmart 检测
    WALMART_ENABLED: bool = os.getenv("WALMART_ENABLED", "true").lower() in ("true", "1")

    # 是否启用价格监控
    PRICE_MONITOR_ENABLED: bool = os.getenv("PRICE_MONITOR_ENABLED", "true").lower() in ("true", "1")

    # Res Sheet 名称（用于记录检测结果）
    RES_SHEET_NAME: str = os.getenv("RES_SHEET_NAME", "Res")

    # 数据源 Sheet 列表（逗号分隔）
    DATA_SHEETS: str = os.getenv("DATA_SHEETS", "WM-FIT,WM-Uriah")

    # 是否启用批量通知
    BATCH_NOTIFICATION_ENABLED: bool = os.getenv("BATCH_NOTIFICATION_ENABLED", "true").lower() in ("true", "1")


class StoreConfig(TypedDict):
    """店铺配置的数据结构"""
    name: str
    refresh_token: str
    lwa_app_id: str
    lwa_client_secret: str
    marketplace_id: str
    aws_access_key_id: str | None
    aws_secret_access_key: str | None


def load_store_configs() -> List[StoreConfig]:
    """
    从 .env 文件中加载所有店铺的配置.

    通过查找以 '_REFRESH_TOKEN' 结尾的环境变量来识别店铺,
    并根据前缀加载相关的凭证.

    Returns:
        一个包含每个店铺配置字典的列表.
    """
    store_configs: List[StoreConfig] = []
    # 识别店铺的主要标识
    refresh_token_suffix = '_REFRESH_TOKEN'

    # 遍历环境变量, 寻找 refresh_token 作为店铺标识
    for key, value in os.environ.items():
        if key.endswith(refresh_token_suffix):
            prefix = key.removesuffix(refresh_token_suffix)

            store_config: Dict[str, str] = {
                'name': prefix,
                'refresh_token': value,
                'lwa_app_id': os.getenv(f'{prefix}_LWA_APP_ID'),
                'lwa_client_secret': os.getenv(f'{prefix}_LWA_CLIENT_SECRET'),
                'marketplace_id': os.getenv(f'{prefix}_MARKETPLACE_ID'),
                'aws_access_key_id': os.getenv(f'{prefix}_AWS_ACCESS_KEY_ID'),
                'aws_secret_access_key': os.getenv(f'{prefix}_AWS_SECRET_ACCESS_KEY'),
            }

            # 验证必要的凭证是否存在
            required_keys = ['lwa_app_id', 'lwa_client_secret', 'marketplace_id']
            if all(store_config.get(k) for k in required_keys):
                store_configs.append(StoreConfig(**store_config))
            else:
                logger.warning(f"Incomplete configuration for store '{prefix}'. Skipping.")

    return store_configs


class ProxyConfig(TypedDict):
    """代理配置的数据结构"""
    enabled: bool
    pool: List[str]


def load_proxy_config() -> ProxyConfig:
    """
    从 .env 文件中加载代理配置.
    """
    proxy_enabled = os.getenv('PROXY_ENABLED', 'false').lower() in ('true', '1')
    proxy_pool_str = os.getenv('PROXY_POOL')

    proxy_pool: List[str] = []
    if proxy_enabled and proxy_pool_str:
        proxy_pool = [proxy.strip() for proxy in proxy_pool_str.split(',')]

    return ProxyConfig(enabled=proxy_enabled, pool=proxy_pool)


def get_random_proxy() -> Optional[str]:
    """
    从代理池中随机选择一个代理.
    """
    config = load_proxy_config()
    if config['enabled'] and config['pool']:
        return random.choice(config['pool'])
    return None


settings = Settings()


if __name__ == '__main__':
    # 用于测试配置加载函数是否正常工作
    setup_logging()
    configs = load_store_configs()
    if configs:
        logger.info(f"Successfully loaded {len(configs)} store configurations:")
        for store_config in configs:
            logger.info(f"- Store: {store_config['name']}")
    else:
        logger.info("No store configurations were loaded.")
