"""
设备管理页面数据模拟服务（兼容层）
专门为设备管理页面生成模拟数据
支持多数据源、分页、定时刷新等功能

注意：本文件已重构为兼容层，实际实现位于 equipment_sim 包中
保留原有 API 接口以确保向后兼容

重构后架构：
- DataSource 抽象基类 + 具体实现（equipment_sim/data_sources.py）
- Generator 纯函数化（equipment_sim/generator.py）
- Scheduler 调度管理（equipment_sim/scheduler.py）
- SideEffectDispatcher 副作用处理（equipment_sim/side_effects.py）
- Service 外观层（equipment_sim/service.py）

新增数据源只需：
1. 继承 BaseDataSource 实现 fetch_data 和 convert
2. 注册到 DataSourceRegistry
"""
from typing import Dict, List, Any, Optional, Tuple

from .equipment_sim.service import EquipmentSimulationService as _ServiceImpl
from .equipment_sim.generator import (
    EQUIPMENT_STATUSES,
    STATUS_WEIGHTS,
    EQUIPMENT_TYPES,
    MANUFACTURERS,
    MODEL_PREFIXES,
    SENSOR_TYPES,
    LOCATIONS,
)


class EquipmentSimulationService:
    """设备管理页面数据模拟服务类（兼容层）

    保留与原文件完全一致的静态方法 API
    内部委托给 equipment_sim 包中的实现
    """

    EQUIPMENT_STATUSES = EQUIPMENT_STATUSES
    STATUS_WEIGHTS = STATUS_WEIGHTS
    EQUIPMENT_TYPES = EQUIPMENT_TYPES
    MANUFACTURERS = MANUFACTURERS
    MODEL_PREFIXES = MODEL_PREFIXES
    SENSOR_TYPES = SENSOR_TYPES
    LOCATIONS = LOCATIONS

    @staticmethod
    def generate_equipment_simulation_data(
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
            source_ids: 数据源ID列表（如果提供，则从指定数据源获取数据）
            use_real_data: 是否使用真实数据库中的数据（如果数据库中有数据）

        Returns:
            (data_dict, total_count): 数据字典和总数量
        """
        return _ServiceImpl.generate_equipment_simulation_data_static(
            page=page,
            size=size,
            line_id=line_id,
            status=status,
            source_ids=source_ids,
            use_real_data=use_real_data,
        )

    @staticmethod
    def get_equipment_simulation_config() -> Dict[str, Any]:
        """获取设备模拟配置"""
        return _ServiceImpl.get_equipment_simulation_config_static()

    @staticmethod
    def start_auto_refresh(interval: int = 30, callback_url: Optional[str] = None):
        """启动自动刷新（模拟实时数据更新）

        Args:
            interval: 刷新间隔（秒）
            callback_url: 回调URL

        Returns:
            后台线程对象
        """
        return _ServiceImpl.start_auto_refresh_static(interval, callback_url)

    @staticmethod
    def create_mock_equipment_data_source(
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
        return _ServiceImpl.create_mock_equipment_data_source_static(source_type, config)
