"""应用心跳定时任务 — 每 5 分钟向算力网络平台上报心跳。

使用 APScheduler BackgroundScheduler 实现轻量级定时任务。
仅当 HEARTBEAT_ENABLED=True 时启动；在 Gunicorn 等多进程部署下，
通过文件锁确保同一台机器上只有一个进程启动心跳调度器。
"""

import logging
import os

logger = logging.getLogger(__name__)

_scheduler = None
_lock_file_handle = None


def _acquire_heartbeat_lock(lock_file):
    """尝试获取心跳文件锁，避免多 worker 重复上报。"""
    global _lock_file_handle

    if not lock_file:
        return True

    try:
        import fcntl
    except ImportError:
        logger.warning("当前平台不支持 fcntl 文件锁，心跳任务无法做多进程去重")
        return True

    try:
        lock_dir = os.path.dirname(lock_file)
        if lock_dir:
            os.makedirs(lock_dir, exist_ok=True)
        handle = open(lock_file, "a+", encoding="utf-8")
    except OSError:
        logger.exception("心跳锁文件打开失败，跳过心跳任务启动: %s", lock_file)
        return False

    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        logger.info("心跳任务已由其他进程持有锁，当前进程跳过启动")
        return False

    handle.seek(0)
    handle.truncate()
    handle.write(f"pid={os.getpid()}\n")
    handle.flush()
    _lock_file_handle = handle
    return True


def _release_heartbeat_lock():
    """释放心跳文件锁。"""
    global _lock_file_handle

    if not _lock_file_handle:
        return

    try:
        import fcntl
        fcntl.flock(_lock_file_handle, fcntl.LOCK_UN)
    except ImportError:
        pass
    finally:
        _lock_file_handle.close()
        _lock_file_handle = None


def start_heartbeat_scheduler(app):
    """启动心跳定时调度器。

    Args:
        app: Flask 应用实例，用于推送应用上下文。
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.info("心跳任务已启动，跳过重复初始化")
        return

    if not app.config.get("HEARTBEAT_ENABLED"):
        logger.info("心跳任务未启用（HEARTBEAT_ENABLED=false）")
        return

    if not app.config.get("PLATFORM_APP_ID") or not app.config.get("PLATFORM_APP_SECRET"):
        logger.warning("心跳任务未配置 PLATFORM_APP_ID 或 PLATFORM_APP_SECRET，跳过启动")
        return

    if not _acquire_heartbeat_lock(app.config.get("HEARTBEAT_LOCK_FILE")):
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        _release_heartbeat_lock()
        logger.error("缺少 apscheduler 依赖，心跳任务无法启动。请运行: pip install apscheduler")
        return

    interval = app.config.get("HEARTBEAT_INTERVAL")
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
    _scheduler = None
    _release_heartbeat_lock()
