"""
调度器层
管理自动刷新任务的调度
使用实例级别的线程管理，消除全局可变状态
"""
import threading
import time
from typing import Any, Callable, Dict, Optional


class RefreshScheduler:
    """自动刷新调度器

    管理定时刷新任务的启动和停止，线程安全
    每个 Service 实例拥有独立的调度器，避免全局状态
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval: int = 30
        self._callback: Optional[Callable[[], Any]] = None
        self._lock = threading.Lock()
        self._is_running = False

    def start(self, interval: int = 30, callback: Optional[Callable[[], Any]] = None,
              callback_url: Optional[str] = None) -> bool:
        """启动自动刷新

        Args:
            interval: 刷新间隔（秒）
            callback: 刷新回调函数
            callback_url: 回调URL（预留，暂未使用）

        Returns:
            是否成功启动
        """
        with self._lock:
            if self._is_running:
                return False

            self._interval = interval
            self._callback = callback
            self._stop_event.clear()
            self._is_running = True

            self._thread = threading.Thread(
                target=self._run,
                daemon=True,
                name=f"RefreshScheduler-{id(self)}"
            )
            self._thread.start()
            return True

    def stop(self) -> bool:
        """停止自动刷新

        Returns:
            是否成功停止
        """
        with self._lock:
            if not self._is_running:
                return False

            self._stop_event.set()
            self._is_running = False

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
            self._thread = None
            return True

    def _run(self):
        """刷新任务主循环"""
        while not self._stop_event.is_set():
            try:
                if self._callback:
                    self._callback()
            except Exception as e:
                print(f"[RefreshScheduler] 刷新任务错误: {e}")

            self._stop_event.wait(self._interval)

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running

    @property
    def interval(self) -> int:
        """当前刷新间隔"""
        return self._interval

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        with self._lock:
            return {
                'is_running': self._is_running,
                'interval': self._interval,
                'has_callback': self._callback is not None,
            }
