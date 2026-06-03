"""应用心跳定时任务 — 每 5 分钟向算力网络平台上报心跳。

使用 APScheduler BackgroundScheduler 实现轻量级定时任务。
仅当 HEARTBEAT_ENABLED=True 时启动。
"""

import logging

from ..config import Config

logger = logging.getLogger(__name__)

_scheduler = None


def start_heartbeat_scheduler(app):
    """启动心跳定时调度器。

    Args:
        app: Flask 应用实例，用于推送应用上下文。
    """
    global _scheduler

    if not Config.HEARTBEAT_ENABLED:
        logger.info("心跳任务未启用（HEARTBEAT_ENABLED=false）")
        return

    if not Config.PLATFORM_APP_ID or not Config.PLATFORM_APP_SECRET:
        logger.warning("心跳任务未配置 PLATFORM_APP_ID 或 PLATFORM_APP_SECRET，跳过启动")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.error("缺少 apscheduler 依赖，心跳任务无法启动。请运行: pip install apscheduler")
        return

    interval = Config.HEARTBEAT_INTERVAL
    _scheduler = BackgroundScheduler(daemon=True)

    def _heartbeat_job():
        """在应用上下文中执行心跳发送。"""
        with app.app_context():
            try:
                from ..services import platform_client
                platform_client.send_heartbeat()
            except Exception:
                logger.exception("心跳发送异常")

    _scheduler.add_job(
        _heartbeat_job,
        "interval",
        seconds=interval,
        id="platform_heartbeat",
        name="算网平台应用心跳",
        max_instances=1,
    )
    _scheduler.start()
    logger.info("心跳定时任务已启动，间隔 %d 秒", interval)


def stop_heartbeat_scheduler():
    """停止心跳定时调度器。"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("心跳定时任务已停止")
