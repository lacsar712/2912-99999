"""
设备模拟主服务层
整合 DataSource、Generator、Scheduler、SideEffectDispatcher 各层
保持与原 EquipmentSimulationService 完全兼容的 API
"""
import random
from typing import Any, Dict, List, Optional, Tuple

from .data_sources import DataSourceManager
from .generator import generate_paginated_equipment, get_simulation_config, paginate_items
from .scheduler import RefreshScheduler
from .side_effects import SideEffectDispatcher


def _default_log_handler(action: str, description: str, **kwargs) -> None:
    """默认日志副作用处理器

    与原实现行为一致：从 flask.g 获取用户信息并写入日志
    如果不在请求上下文中，则使用默认值
    """
    try:
        from models.log import Log
        from flask import g

        user_id = g.user_id if hasattr(g, 'user_id') else 0
        username = g.username if hasattr(g, 'username') else 'system'
    except Exception:
        user_id = 0
        username = 'system'

    try:
        Log.add_log(user_id, username, action, 'equipment_simulation', description)
    except Exception:
        pass


def _create_default_dispatcher() -> SideEffectDispatcher:
    """创建默认副作用派发器（带有日志处理器）

    为了与原实现行为保持一致，默认注册日志处理器
    """
    dispatcher = SideEffectDispatcher()
    dispatcher.register_handler('log', _default_log_handler)
    return dispatcher


class EquipmentSimulationService:
    """设备管理页面数据模拟服务类

    重构后：作为外观层(Facade)，整合各子系统
    - 数据生成：委托给 generator 纯函数
    - 数据源：委托给 DataSourceManager
    - 调度：委托给 RefreshScheduler
    - 副作用：委托给 SideEffectDispatcher

    保持与原 API 完全兼容，所有静态方法均正常工作
    """

    # 类级别的默认实例，用于静态方法调用
    _default_instance: Optional['EquipmentSimulationService'] = None

    def __init__(
        self,
        data_source_manager: Optional[DataSourceManager] = None,
        scheduler: Optional[RefreshScheduler] = None,
        side_effect_dispatcher: Optional[SideEffectDispatcher] = None,
        rng: Optional[random.Random] = None,
    ):
        self._data_source_manager = data_source_manager or DataSourceManager()
        self._scheduler = scheduler or RefreshScheduler()
        self._side_effects = side_effect_dispatcher or _create_default_dispatcher()
        self._rng = rng or random.Random()

    @classmethod
    def _get_instance(cls) -> 'EquipmentSimulationService':
        """获取默认单例（用于静态方法兼容）

        注意：这是为了保持与原有静态方法 API 的兼容性
        新代码应直接实例化 EquipmentSimulationService
        """
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    @classmethod
    def _reset_instance(cls):
        """重置默认实例（用于测试）"""
        cls._default_instance = None

    # ============= 数据源管理 =============

    @property
    def data_source_manager(self) -> DataSourceManager:
        """获取数据源管理器"""
        return self._data_source_manager

    # ============= 数据生成 =============

    def generate_equipment_simulation_data(
        self,
        page: int = 1,
        size: int = 10,
        line_id: Optional[int] = None,
        status: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        use_real_data: bool = False,
    ) -> Tuple[Dict, int]:
        """生成设备模拟数据

        Args:
            page: 页码
            size: 每页大小
            line_id: 生产线ID筛选
            status: 设备状态筛选
            source_ids: 数据源ID列表
            use_real_data: 是否使用真实数据库中的数据

        Returns:
            (data_dict, total_count): 数据字典和总数量
        """
        if use_real_data:
            return self._get_real_equipment_data(page, size, line_id, status)

        if source_ids:
            return self._get_data_from_sources(source_ids, page, size)

        return self._generate_mock_equipment_data(page, size, line_id, status)

    def _get_real_equipment_data(
        self,
        page: int,
        size: int,
        line_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Tuple[Dict, int]:
        """获取真实数据库中的设备数据"""
        from services.production_service import EquipmentService
        from database.db import db
        from models.production import Equipment

        query = Equipment.query.filter(Equipment.status != 0)

        if line_id:
            query = query.filter(Equipment.line_id == line_id)
        if status:
            query = query.filter(Equipment.status == status)

        total = query.count()
        pagination = query.order_by(Equipment.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = []
        for equipment in pagination.items:
            item = equipment.to_dict()
            item['sensor_count'] = equipment.sensors.count()
            item['running_sensor_count'] = equipment.sensors.filter_by(status='normal').count()
            item['warning_sensor_count'] = equipment.sensors.filter_by(status='warning').count()
            items.append(item)

        return {
            'items': items,
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size if size > 0 else 0
        }, total

    def _generate_mock_equipment_data(
        self,
        page: int,
        size: int,
        line_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Tuple[Dict, int]:
        """生成模拟设备数据（委托给 generator）"""
        return generate_paginated_equipment(
            page=page,
            size=size,
            rng=self._rng,
            line_id=line_id,
            status=status,
        )

    def _get_data_from_sources(
        self,
        source_ids: List[str],
        page: int,
        size: int,
    ) -> Tuple[Dict, int]:
        """从指定数据源获取设备数据"""
        all_items = self._data_source_manager.fetch_from_sources(source_ids, size)
        data = paginate_items(all_items, page, size)
        return data, len(all_items)

    # ============= 配置 =============

    def get_equipment_simulation_config(self) -> Dict[str, Any]:
        """获取设备模拟配置"""
        return get_simulation_config()

    # ============= 调度 =============

    def start_auto_refresh(self, interval: int = 30, callback_url: Optional[str] = None):
        """启动自动刷新

        Args:
            interval: 刷新间隔（秒）
            callback_url: 回调URL

        Returns:
            刷新线程对象
        """
        def refresh_callback():
            try:
                if callback_url:
                    pass
            except Exception as e:
                print(f"自动刷新任务错误: {e}")

        self._scheduler.start(interval=interval, callback=refresh_callback, callback_url=callback_url)
        return self._scheduler._thread

    def stop_auto_refresh(self) -> bool:
        """停止自动刷新"""
        return self._scheduler.stop()

    @property
    def scheduler(self) -> RefreshScheduler:
        """获取调度器"""
        return self._scheduler

    # ============= 副作用 =============

    def create_mock_equipment_data_source(
        self,
        source_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """创建设备模拟数据源

        Args:
            source_type: 数据源类型
            config: 数据源配置

        Returns:
            操作结果字典
        """
        try:
            source_info = self._data_source_manager.create_source(source_type, config)
            source_id = source_info['source_id']

            self._side_effects.dispatch(
                'log',
                action='create',
                description=f'创建设备模拟数据源: {source_type} ({source_id})',
            )

            return {
                'source_id': source_id,
                'type': source_type,
                'config': config,
                'status': 'created'
            }

        except Exception as e:
            return {
                'error': f'创建设备模拟数据源失败: {str(e)}',
                'status': 'error'
            }

    @property
    def side_effects(self) -> SideEffectDispatcher:
        """获取副作用派发器"""
        return self._side_effects

    # ============= 静态方法（保持 API 兼容） =============

    @staticmethod
    def generate_equipment_simulation_data_static(
        page: int = 1,
        size: int = 10,
        line_id: Optional[int] = None,
        status: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        use_real_data: bool = False,
    ) -> Tuple[Dict, int]:
        """生成设备模拟数据（静态方法版本，保持兼容）"""
        service = EquipmentSimulationService._get_instance()
        return service.generate_equipment_simulation_data(
            page=page,
            size=size,
            line_id=line_id,
            status=status,
            source_ids=source_ids,
            use_real_data=use_real_data,
        )

    @staticmethod
    def get_equipment_simulation_config_static() -> Dict[str, Any]:
        """获取设备模拟配置（静态方法版本，保持兼容）"""
        service = EquipmentSimulationService._get_instance()
        return service.get_equipment_simulation_config()

    @staticmethod
    def start_auto_refresh_static(interval: int = 30, callback_url: Optional[str] = None):
        """启动自动刷新（静态方法版本，保持兼容）"""
        service = EquipmentSimulationService._get_instance()
        return service.start_auto_refresh(interval, callback_url)

    @staticmethod
    def create_mock_equipment_data_source_static(
        source_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """创建设备模拟数据源（静态方法版本，保持兼容）"""
        service = EquipmentSimulationService._get_instance()
        return service.create_mock_equipment_data_source(source_type, config)

    # ============= 兼容性：静态方法名与原文件一致 =============
    # 注意：为了保持与原文件完全一致的 API，
    # 以下方法名与原文件中的静态方法名相同
    # 但因为它们是实例方法（为了使用实例状态），
    # 我们在 equipment_simulation_service.py 兼容层中做了处理
