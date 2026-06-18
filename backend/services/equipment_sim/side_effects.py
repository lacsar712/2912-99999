"""
副作用派发器层
集中处理写库、告警、日志等副作用操作
将副作用与业务逻辑解耦，便于测试和替换实现
"""
from typing import Any, Callable, Dict, List, Optional


class SideEffectDispatcher:
    """副作用派发器

    集中管理所有副作用操作（写日志、触发告警、写数据库等）
    支持注册和替换各种副作用处理器，便于测试时 mock
    """

    def __init__(self):
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._enabled = True

    def register_handler(self, name: str, handler: Callable[..., Any]):
        """注册副作用处理器

        Args:
            name: 处理器名称
            handler: 处理函数
        """
        self._handlers[name] = handler

    def unregister_handler(self, name: str) -> bool:
        """取消注册副作用处理器

        Args:
            name: 处理器名称

        Returns:
            是否成功移除
        """
        return self._handlers.pop(name, None) is not None

    def dispatch(self, name: str, *args, **kwargs) -> Optional[Any]:
        """派发副作用

        Args:
            name: 处理器名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            处理器返回值（如果有）
        """
        if not self._enabled:
            return None

        handler = self._handlers.get(name)
        if handler is None:
            return None

        try:
            return handler(*args, **kwargs)
        except Exception as e:
            print(f"[SideEffectDispatcher] 处理器 {name} 执行错误: {e}")
            return None

    def has_handler(self, name: str) -> bool:
        """检查是否有指定的处理器"""
        return name in self._handlers

    def set_enabled(self, enabled: bool):
        """启用/禁用所有副作用

        Args:
            enabled: 是否启用
        """
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    def list_handlers(self) -> List[str]:
        """列出所有已注册的处理器名称"""
        return list(self._handlers.keys())


# ============= 预设副作用处理器 =============

def create_log_handler(user_id: Optional[int] = None, username: Optional[str] = None,
                       module: str = 'equipment_simulation') -> Callable:
    """创建操作日志副作用处理器

    Args:
        user_id: 用户ID
        username: 用户名
        module: 模块名

    Returns:
        日志处理函数
    """
    def log_handler(action: str, description: str, **kwargs):
        from models.log import Log
        uid = kwargs.get('user_id', user_id) or 0
        uname = kwargs.get('username', username) or 'system'
        Log.add_log(uid, uname, action, module, description)
    return log_handler


def create_alert_handler() -> Callable:
    """创建告警副作用处理器

    Returns:
        告警处理函数
    """
    def alert_handler(alert_data: Dict[str, Any], **kwargs):
        from services.alert_service import AlertService
        return AlertService.create_alert(alert_data)
    return alert_handler


def create_equipment_write_handler() -> Callable:
    """创建设备数据写入副作用处理器

    Returns:
        设备数据写入处理函数
    """
    def write_handler(equipment_data: Dict[str, Any], **kwargs):
        from database.db import db
        from models.production import Equipment
        # 预留：将模拟数据写入真实数据库
        pass
    return write_handler


def setup_default_dispatcher(user_id: Optional[int] = None,
                             username: Optional[str] = None) -> SideEffectDispatcher:
    """创建并配置默认的副作用派发器

    Args:
        user_id: 用户ID
        username: 用户名

    Returns:
        配置好的 SideEffectDispatcher 实例
    """
    dispatcher = SideEffectDispatcher()
    dispatcher.register_handler('log', create_log_handler(user_id, username))
    dispatcher.register_handler('alert', create_alert_handler())
    dispatcher.register_handler('write_equipment', create_equipment_write_handler())
    return dispatcher
