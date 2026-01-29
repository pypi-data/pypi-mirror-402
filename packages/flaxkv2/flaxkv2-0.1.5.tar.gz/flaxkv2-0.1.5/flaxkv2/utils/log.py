"""
FlaxKV2 日志模块

作为基础库，遵循以下日志最佳实践：
1. 使用标准 logging 模块，命名空间隔离（flaxkv2.*）
2. 默认静默（NullHandler），不影响应用程序
3. 通过环境变量 FLAXKV_ENABLE_LOGGING=1 可以启用日志
4. 应用程序可以调用 enable_logging() 来启用日志
5. 支持多进程安全的文件日志（multiprocess_safe=True）
"""

import atexit
import logging
import os
import sys
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from multiprocessing import Queue as MPQueue
from typing import List, Optional, Tuple, Union

# 默认格式
_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

# 创建 flaxkv2 命名空间的根 logger
_root_logger = logging.getLogger("flaxkv2")
_root_logger.addHandler(logging.NullHandler())  # 库的标准做法：默认静默

# 存储 flaxkv2 专用 handler
_flaxkv2_handler: Optional[logging.Handler] = None

# 多进程日志支持
_mp_queue: Optional[MPQueue] = None
_mp_listener: Optional[QueueListener] = None
_mp_handlers: List[logging.Handler] = []


def _get_level(level: str) -> int:
    """将字符串级别转换为 logging 常量"""
    return getattr(logging, level.upper(), logging.INFO)


def _cleanup_mp_logging() -> None:
    """清理多进程日志资源"""
    global _mp_listener, _mp_queue, _mp_handlers
    if _mp_listener is not None:
        try:
            # 发送 sentinel 通知 listener 停止
            if _mp_queue is not None:
                _mp_queue.put_nowait(None)
            _mp_listener.stop()
        except Exception:
            pass
        _mp_listener = None
        _mp_handlers.clear()


# 注册退出清理
atexit.register(_cleanup_mp_logging)


# 检查是否通过环境变量启用日志
if os.environ.get("FLAXKV_ENABLE_LOGGING", "0") == "1":
    _DEFAULT_LOG_LEVEL = os.environ.get("FLAXKV_LOG_LEVEL", "WARNING")
    _flaxkv2_handler = logging.StreamHandler(sys.stderr)
    _flaxkv2_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
    _flaxkv2_handler.setLevel(_get_level(_DEFAULT_LOG_LEVEL))
    _root_logger.addHandler(_flaxkv2_handler)
    _root_logger.setLevel(_get_level(_DEFAULT_LOG_LEVEL))


def enable_logging(level: str = "INFO", format_str: Optional[str] = None) -> None:
    """
    启用 FlaxKV2 日志输出（供应用程序调用）

    Args:
        level: 日志级别，默认 'INFO'
        format_str: 自定义格式字符串，None 则使用默认格式

    Example:
        >>> from flaxkv2.utils.log import enable_logging
        >>> enable_logging(level="DEBUG")
    """
    global _flaxkv2_handler

    # 移除旧的 handler（如果存在）
    if _flaxkv2_handler is not None:
        _root_logger.removeHandler(_flaxkv2_handler)
        _flaxkv2_handler = None

    if format_str is None:
        format_str = _DEFAULT_FORMAT

    # 创建新的 handler
    _flaxkv2_handler = logging.StreamHandler(sys.stderr)
    _flaxkv2_handler.setFormatter(logging.Formatter(format_str))
    _flaxkv2_handler.setLevel(_get_level(level))

    _root_logger.addHandler(_flaxkv2_handler)
    _root_logger.setLevel(_get_level(level))


def disable_logging() -> None:
    """
    禁用 FlaxKV2 日志输出

    Example:
        >>> from flaxkv2.utils.log import disable_logging
        >>> disable_logging()
    """
    global _flaxkv2_handler

    if _flaxkv2_handler is not None:
        _root_logger.removeHandler(_flaxkv2_handler)
        _flaxkv2_handler = None

    # 设置为最高级别，有效禁用日志
    _root_logger.setLevel(logging.CRITICAL + 1)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger（命名空间隔离）

    Args:
        name: 日志名称，通常为模块名（如 __name__）

    Returns:
        logger: 配置好的 logger 实例
    """
    # 如果已经是 flaxkv2 开头，直接使用
    if name.startswith("flaxkv2"):
        return logging.getLogger(name)
    # 否则添加 flaxkv2 前缀
    return logging.getLogger(f"flaxkv2.{name}")


def set_log_level(level: str) -> None:
    """
    设置日志级别

    Args:
        level: 日志级别，如 'DEBUG', 'INFO', 'WARNING', 'ERROR'

    Note:
        如果日志未启用，会自动启用并设置指定级别
    """
    global _flaxkv2_handler

    log_level = _get_level(level)

    # 如果没有 handler，先启用日志
    if _flaxkv2_handler is None:
        enable_logging(level=level)
    else:
        _flaxkv2_handler.setLevel(log_level)
        _root_logger.setLevel(log_level)


def _parse_rotation(rotation: str) -> int:
    """解析 rotation 参数为 maxBytes"""
    max_bytes = 10 * 1024 * 1024  # 默认 10MB
    if rotation:
        rotation = rotation.strip().upper()
        if "MB" in rotation:
            try:
                max_bytes = int(float(rotation.replace("MB", "").strip()) * 1024 * 1024)
            except ValueError:
                pass
        elif "KB" in rotation:
            try:
                max_bytes = int(float(rotation.replace("KB", "").strip()) * 1024)
            except ValueError:
                pass
    return max_bytes


def _parse_retention(retention: str) -> int:
    """解析 retention 参数为 backupCount"""
    backup_count = 7  # 默认保留 7 个备份
    if retention:
        retention = retention.strip().lower()
        if "days" in retention:
            try:
                backup_count = int(retention.replace("days", "").strip())
            except ValueError:
                pass
    return backup_count


def add_file_log(
    filepath: str,
    level: str = "DEBUG",
    rotation: str = "10 MB",
    retention: str = "7 days",
    multiprocess_safe: bool = True
) -> logging.Handler:
    """
    添加文件日志记录

    Args:
        filepath: 日志文件路径
        level: 日志级别
        rotation: 日志轮转大小（如 "10 MB"）
        retention: 保留备份数（从 days 参数解析，如 "7 days" -> 保留 7 个备份）
        multiprocess_safe: 是否启用多进程安全模式，默认 True

    Returns:
        handler: 可用于后续移除该 handler

    Note:
        - 多进程模式（默认）：使用 QueueHandler + QueueListener，进程安全
        - 单进程模式：设置 multiprocess_safe=False，性能略好
    """
    global _mp_queue, _mp_listener, _mp_handlers

    max_bytes = _parse_rotation(rotation)
    backup_count = _parse_retention(retention)

    # 创建文件 handler
    file_handler = RotatingFileHandler(
        filepath,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
    file_handler.setLevel(_get_level(level))

    log_level = _get_level(level)

    if multiprocess_safe:
        # 多进程安全模式：使用 QueueHandler
        if _mp_queue is None:
            _mp_queue = MPQueue(-1)  # 无限队列

        # 创建 QueueHandler 给 logger 使用
        queue_handler = QueueHandler(_mp_queue)
        queue_handler.setLevel(log_level)
        _root_logger.addHandler(queue_handler)

        # 将文件 handler 添加到 listener 管理列表
        _mp_handlers.append(file_handler)

        # 重新创建 listener（包含所有 handlers）
        if _mp_listener is not None:
            _mp_listener.stop()

        _mp_listener = QueueListener(_mp_queue, *_mp_handlers, respect_handler_level=True)
        _mp_listener.start()

        # 设置 root logger 级别（NOTSET=0 时也需要设置）
        if _root_logger.level == logging.NOTSET or _root_logger.level > log_level:
            _root_logger.setLevel(log_level)

        return queue_handler
    else:
        # 单进程模式：直接添加文件 handler
        _root_logger.addHandler(file_handler)

        # 设置 root logger 级别（NOTSET=0 时也需要设置）
        if _root_logger.level == logging.NOTSET or _root_logger.level > log_level:
            _root_logger.setLevel(log_level)

        return file_handler


def get_multiprocess_queue() -> Optional[MPQueue]:
    """
    获取多进程日志队列（供子进程使用）

    在主进程调用 add_file_log(multiprocess_safe=True) 后，
    子进程可以通过此函数获取队列，并配置自己的 QueueHandler。

    Returns:
        队列对象，如果未启用多进程模式则返回 None

    Example:
        # 主进程
        from flaxkv2.utils.log import add_file_log, get_multiprocess_queue
        add_file_log("app.log", multiprocess_safe=True)
        queue = get_multiprocess_queue()

        # 传递 queue 给子进程，子进程中：
        from flaxkv2.utils.log import setup_worker_logging
        setup_worker_logging(queue)
    """
    return _mp_queue


def setup_worker_logging(queue: MPQueue, level: str = "DEBUG") -> None:
    """
    在子进程中配置日志（使用主进程的队列）

    Args:
        queue: 从主进程获取的日志队列
        level: 日志级别

    Example:
        # 在子进程中
        from flaxkv2.utils.log import setup_worker_logging
        setup_worker_logging(queue, level="INFO")
    """
    # 移除现有 handlers
    _root_logger.handlers.clear()

    # 添加 QueueHandler
    queue_handler = QueueHandler(queue)
    queue_handler.setLevel(_get_level(level))
    _root_logger.addHandler(queue_handler)
    _root_logger.setLevel(_get_level(level))
