"""
系统韧性模块
提供组件健康检查、降级模式管理与自愈记录
"""
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from database.db import db
from utils.logger import logger


class SelfHealLog:
    _records: List[Dict[str, Any]] = []
    _lock = threading.Lock()
    _max_records = 200

    @classmethod
    def append(cls, component: str, event: str, detail: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "event": event,
            "detail": detail,
        }
        with cls._lock:
            cls._records.append(entry)
            if len(cls._records) > cls._max_records:
                cls._records = cls._records[-cls._max_records:]
        logger.info(f"[SelfHeal] {component} {event}: {detail}")

    @classmethod
    def recent(cls, limit: int = 50) -> List[Dict[str, Any]]:
        with cls._lock:
            return list(cls._records[-limit:])


class ComponentHealthChecker:
    @staticmethod
    def check_database() -> Dict[str, Any]:
        try:
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            return {"status": "healthy", "component": "database", "detail": None}
        except Exception as e:
            return {"status": "unhealthy", "component": "database", "detail": str(e)}

    @staticmethod
    def check_redis() -> Dict[str, Any]:
        try:
            import redis as _redis
            from config import Config

            r = _redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            r.ping()
            return {"status": "healthy", "component": "redis", "detail": None}
        except Exception as e:
            return {"status": "unhealthy", "component": "redis", "detail": str(e)}

    @staticmethod
    def check_simulation() -> Dict[str, Any]:
        try:
            scheduler_running = any(
                t.name == "main-scheduler" and t.is_alive()
                for t in threading.enumerate()
            )
            return {
                "status": "healthy" if scheduler_running else "degraded",
                "component": "simulation",
                "detail": None if scheduler_running else "simulation scheduler not running",
            }
        except Exception as e:
            return {"status": "unhealthy", "component": "simulation", "detail": str(e)}

    @classmethod
    def check_all(cls) -> Dict[str, Any]:
        results = {
            "database": cls.check_database(),
            "redis": cls.check_redis(),
            "simulation": cls.check_simulation(),
        }
        overall = "healthy"
        for r in results.values():
            if r["status"] == "unhealthy":
                overall = "unhealthy"
                break
            if r["status"] == "degraded" and overall == "healthy":
                overall = "degraded"
        return {"status": overall, "components": results}


class DegradationManager:
    _instance: Optional["DegradationManager"] = None

    def __init__(self):
        self._states: Dict[str, str] = {
            "database": "healthy",
            "redis": "healthy",
            "simulation": "healthy",
        }
        self._lock = threading.Lock()
        self._consecutive_failures: Dict[str, int] = {
            "database": 0,
            "redis": 0,
            "simulation": 0,
        }
        self._failure_threshold = 3
        self._recovery_threshold = 2
        self._consecutive_successes: Dict[str, int] = {
            "database": 0,
            "redis": 0,
            "simulation": 0,
        }

    @classmethod
    def get_instance(cls) -> "DegradationManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    @property
    def states(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._states)

    def is_database_available(self) -> bool:
        with self._lock:
            return self._states["database"] != "down"

    def is_redis_available(self) -> bool:
        with self._lock:
            return self._states["redis"] != "down"

    def is_simulation_available(self) -> bool:
        with self._lock:
            return self._states["simulation"] != "down"

    def is_read_only(self) -> bool:
        with self._lock:
            return self._states["database"] == "down"

    def get_degraded_components(self) -> List[str]:
        with self._lock:
            return [k for k, v in self._states.items() if v != "healthy"]

    def get_degradation_info(self) -> Dict[str, Any]:
        with self._lock:
            info = {}
            for component, state in self._states.items():
                info[component] = {
                    "state": state,
                    "consecutive_failures": self._consecutive_failures.get(component, 0),
                    "consecutive_successes": self._consecutive_successes.get(component, 0),
                }
            return info

    def update(self, health_results: Dict[str, Dict[str, Any]]):
        with self._lock:
            for component, result in health_results.items():
                if component not in self._states:
                    continue
                status = result.get("status", "unhealthy")
                old_state = self._states[component]

                if status == "healthy":
                    self._consecutive_failures[component] = 0
                    self._consecutive_successes[component] += 1
                    if old_state == "down" and self._consecutive_successes[component] >= self._recovery_threshold:
                        self._states[component] = "healthy"
                        SelfHealLog.append(
                            component, "recovered",
                            f"{component} has recovered to healthy after {self._recovery_threshold} consecutive successes"
                        )
                    elif old_state != "healthy" and old_state != "down":
                        self._states[component] = "healthy"
                        SelfHealLog.append(
                            component, "recovered",
                            f"{component} has recovered to healthy"
                        )
                elif status == "degraded":
                    self._consecutive_failures[component] = 0
                    self._consecutive_successes[component] = 0
                    if old_state != "degraded":
                        self._states[component] = "degraded"
                        SelfHealLog.append(
                            component, "degraded",
                            f"{component} entered degraded mode: {result.get('detail', '')}"
                        )
                else:
                    self._consecutive_successes[component] = 0
                    self._consecutive_failures[component] += 1
                    if self._consecutive_failures[component] >= self._failure_threshold:
                        if old_state != "down":
                            self._states[component] = "down"
                            SelfHealLog.append(
                                component, "down",
                                f"{component} marked as down after {self._failure_threshold} consecutive failures: {result.get('detail', '')}"
                            )
                    else:
                        if old_state == "healthy":
                            self._states[component] = "degraded"
                            SelfHealLog.append(
                                component, "degraded",
                                f"{component} degraded due to health check failure ({self._consecutive_failures[component]}/{self._failure_threshold}): {result.get('detail', '')}"
                            )


def start_resilience_monitor(app, interval: int = 15):
    dm = DegradationManager.get_instance()

    def _loop():
        with app.app_context():
            while True:
                try:
                    result = ComponentHealthChecker.check_all()
                    dm.update(result["components"])
                except Exception as e:
                    logger.error(f"[Resilience] health check loop error: {e}")
                time.sleep(interval)

    thread = threading.Thread(target=_loop, daemon=True, name="resilience-monitor")
    thread.start()
    logger.info(f"[Resilience] monitor started (interval={interval}s)")
    return thread
