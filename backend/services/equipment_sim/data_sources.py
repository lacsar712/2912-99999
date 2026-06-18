"""
数据源层
定义 DataSource 抽象基类及具体实现
新增数据源只需继承 BaseDataSource 并注册到 DataSourceRegistry
"""
import random
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class BaseDataSource(ABC):
    """数据源抽象基类

    所有设备数据源都需要继承此类并实现 fetch_data 和 convert 方法
    """

    source_type: str = "base"

    def __init__(self, source_id: str, config: Optional[Dict[str, Any]] = None):
        self.source_id = source_id
        self.config = config or {}
        self._created_at = datetime.now().isoformat()

    @abstractmethod
    def fetch_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """从数据源获取原始数据

        Args:
            count: 获取数据条数

        Returns:
            原始数据列表
        """
        raise NotImplementedError

    @abstractmethod
    def convert(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将原始数据转换为标准设备格式

        Args:
            raw_data: 原始数据列表

        Returns:
            标准化的设备数据列表
        """
        raise NotImplementedError

    def get_equipment_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取并转换设备数据（模板方法）

        Args:
            count: 数据条数

        Returns:
            标准化设备数据列表
        """
        raw = self.fetch_data(count)
        return self.convert(raw)

    def to_dict(self) -> Dict[str, Any]:
        """获取数据源元信息"""
        return {
            'source_id': self.source_id,
            'type': self.source_type,
            'name': self.config.get('name', f'{self.source_type} 数据源'),
            'description': self.config.get('description', ''),
            'status': self.config.get('status', 'active'),
            'config': self.config,
            'created_at': self._created_at,
        }


class ApiDataSource(BaseDataSource):
    """API 数据源实现"""

    source_type: str = "api"

    def fetch_data(self, count: int = 10) -> List[Dict[str, Any]]:
        return [
            {'value': random.uniform(0, 100), 'source_id': self.source_id}
            for _ in range(count)
        ]

    def convert(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        equipment_list = []
        for i, item in enumerate(raw_data):
            equipment_list.append({
                'id': i + 1000,
                'equipment_code': f'API-EQP-{i}',
                'equipment_name': f'API设备{i}',
                'equipment_type': 'API设备',
                'line_id': random.randint(1, 3),
                'line_name': f'生产线{random.randint(1, 3)}',
                'status': random.choice(['running', 'idle']),
                'model': 'API-MODEL',
                'manufacturer': 'API厂商',
                'runtime_hours': round(random.uniform(100, 5000), 2),
                'temperature': round(random.uniform(20, 60), 2),
                'pressure': round(random.uniform(10, 70), 2),
                'speed': round(random.uniform(0, 2000), 2),
                'sensor_count': random.randint(2, 6),
                'running_sensor_count': random.randint(2, 6),
                'warning_sensor_count': random.randint(0, 1),
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return equipment_list


class WebSocketDataSource(BaseDataSource):
    """WebSocket 数据源实现"""

    source_type: str = "websocket"

    def fetch_data(self, count: int = 10) -> List[Dict[str, Any]]:
        return [
            {'value': random.uniform(0, 100), 'source_id': self.source_id}
            for _ in range(count)
        ]

    def convert(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        equipment_list = []
        for i, item in enumerate(raw_data):
            equipment_list.append({
                'id': i + 2000,
                'equipment_code': f'WS-EQP-{i}',
                'equipment_name': f'WebSocket设备{i}',
                'equipment_type': '实时设备',
                'line_id': random.randint(1, 3),
                'line_name': f'生产线{random.randint(1, 3)}',
                'status': 'running',
                'model': 'WS-MODEL',
                'manufacturer': 'WS厂商',
                'runtime_hours': round(random.uniform(500, 8000), 2),
                'temperature': round(random.uniform(25, 70), 2),
                'pressure': round(random.uniform(20, 80), 2),
                'speed': round(random.uniform(500, 2500), 2),
                'sensor_count': random.randint(4, 8),
                'running_sensor_count': random.randint(3, 7),
                'warning_sensor_count': random.randint(0, 2),
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return equipment_list


class FileStreamDataSource(BaseDataSource):
    """文件流数据源实现"""

    source_type: str = "file_stream"

    def fetch_data(self, count: int = 10) -> List[Dict[str, Any]]:
        return [
            {'value': random.uniform(0, 100), 'source_id': self.source_id}
            for _ in range(count)
        ]

    def convert(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        equipment_list = []
        for i, item in enumerate(raw_data):
            equipment_list.append({
                'id': i + 3000,
                'equipment_code': f'FILE-EQP-{i}',
                'equipment_name': f'文件设备{i}',
                'equipment_type': '文件设备',
                'line_id': random.randint(1, 3),
                'line_name': f'生产线{random.randint(1, 3)}',
                'status': random.choice(['running', 'idle', 'offline']),
                'model': 'FILE-MODEL',
                'manufacturer': '文件厂商',
                'runtime_hours': round(random.uniform(0, 3000), 2),
                'temperature': round(random.uniform(15, 40), 2),
                'pressure': round(random.uniform(0, 50), 2),
                'speed': round(random.uniform(0, 1000), 2),
                'sensor_count': random.randint(1, 4),
                'running_sensor_count': random.randint(0, 3),
                'warning_sensor_count': random.randint(0, 2),
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return equipment_list


class UserInputDataSource(BaseDataSource):
    """用户输入数据源实现"""

    source_type: str = "user_input"

    def fetch_data(self, count: int = 10) -> List[Dict[str, Any]]:
        return [
            {'value': random.uniform(0, 100), 'source_id': self.source_id}
            for _ in range(count)
        ]

    def convert(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        equipment_list = []
        for i, item in enumerate(raw_data):
            equipment_list.append({
                'id': i + 4000,
                'equipment_code': f'USER-EQP-{i}',
                'equipment_name': f'用户设备{i}',
                'equipment_type': '用户设备',
                'line_id': random.randint(1, 3),
                'line_name': f'生产线{random.randint(1, 3)}',
                'status': random.choice(['running', 'idle', 'maintenance']),
                'model': 'USER-MODEL',
                'manufacturer': '用户厂商',
                'runtime_hours': round(random.uniform(100, 2000), 2),
                'temperature': round(random.uniform(20, 50), 2),
                'pressure': round(random.uniform(10, 60), 2),
                'speed': round(random.uniform(0, 1500), 2),
                'sensor_count': random.randint(2, 5),
                'running_sensor_count': random.randint(1, 4),
                'warning_sensor_count': random.randint(0, 2),
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return equipment_list


class GenericDataSource(BaseDataSource):
    """通用默认数据源实现"""

    source_type: str = "generic"

    def fetch_data(self, count: int = 10) -> List[Dict[str, Any]]:
        return [
            {'value': random.uniform(0, 100), 'source_id': self.source_id}
            for _ in range(count)
        ]

    def convert(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        equipment_list = []
        for i, item in enumerate(raw_data):
            equipment_list.append({
                'id': i + 5000,
                'equipment_code': f'SRC-{self.source_id[:8]}-{i}',
                'equipment_name': f'数据源设备{i}',
                'equipment_type': '通用设备',
                'line_id': 1,
                'line_name': '生产线1',
                'status': 'running',
                'model': 'GENERIC',
                'manufacturer': '通用厂商',
                'runtime_hours': 1000.0,
                'temperature': 25.0,
                'pressure': 50.0,
                'speed': 1000.0,
                'sensor_count': 4,
                'running_sensor_count': 3,
                'warning_sensor_count': 1,
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return equipment_list


class DataSourceRegistry:
    """数据源注册表

    管理数据源类型到实现类的映射，支持动态注册新数据源
    使用实例级别的存储，消除全局可变状态
    """

    def __init__(self):
        self._registry: Dict[str, type] = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册默认数据源类型"""
        self.register('api', ApiDataSource)
        self.register('websocket', WebSocketDataSource)
        self.register('file_stream', FileStreamDataSource)
        self.register('user_input', UserInputDataSource)
        self.register('generic', GenericDataSource)

    def register(self, source_type: str, cls: type):
        """注册数据源类型

        Args:
            source_type: 数据源类型标识
            cls: 数据源实现类（需继承 BaseDataSource）
        """
        if not issubclass(cls, BaseDataSource):
            raise ValueError(f"数据源类 {cls.__name__} 必须继承 BaseDataSource")
        self._registry[source_type] = cls

    def get_class(self, source_type: str) -> type:
        """获取数据源实现类

        Args:
            source_type: 数据源类型标识

        Returns:
            对应的数据源实现类，不存在则返回 GenericDataSource
        """
        return self._registry.get(source_type, GenericDataSource)

    def create(self, source_type: str, source_id: Optional[str] = None,
               config: Optional[Dict[str, Any]] = None) -> BaseDataSource:
        """创建数据源实例

        Args:
            source_type: 数据源类型
            source_id: 数据源ID，不提供则自动生成
            config: 数据源配置

        Returns:
            数据源实例
        """
        cls = self.get_class(source_type)
        if source_id is None:
            source_id = f"{source_type}_{uuid.uuid4().hex[:8]}"
        return cls(source_id, config)

    def has_type(self, source_type: str) -> bool:
        """检查是否支持某种数据源类型"""
        return source_type in self._registry

    def list_types(self) -> List[str]:
        """列出所有已注册的数据源类型"""
        return list(self._registry.keys())


class DataSourceManager:
    """数据源实例管理器

    管理多个数据源实例的生命周期，线程安全
    使用实例级别的存储，每个 Service 实例拥有独立的管理器
    """

    def __init__(self, registry: Optional[DataSourceRegistry] = None):
        self._registry = registry or DataSourceRegistry()
        self._sources: Dict[str, BaseDataSource] = {}
        import threading
        self._lock = threading.Lock()
        self._init_default_sources()

    def _init_default_sources(self):
        """初始化默认数据源"""
        defaults = [
            {
                'source_id': 'api_default',
                'type': 'api',
                'name': '设备API数据源',
                'description': '通过 REST API 定期获取设备数据',
                'status': 'active',
                'endpoint': '/api/simulation/equipment/data',
                'method': 'GET',
                'interval': 5,
            },
            {
                'source_id': 'websocket_default',
                'type': 'websocket',
                'name': '设备WebSocket数据源',
                'description': '实时推送设备状态数据',
                'status': 'active',
                'url': 'ws://localhost:5001/ws/equipment',
                'interval': 1,
            },
            {
                'source_id': 'file_stream_default',
                'type': 'file_stream',
                'name': '设备文件流数据源',
                'description': '从 CSV/JSON 文件读取设备数据',
                'status': 'active',
                'format': 'csv',
                'interval': 10,
            },
            {
                'source_id': 'user_input_default',
                'type': 'user_input',
                'name': '设备人工录入数据源',
                'description': '通过表单手工录入设备数据',
                'status': 'active',
            },
        ]
        for source_config in defaults:
            source_type = source_config.pop('type')
            source_id = source_config.pop('source_id')
            self._sources[source_id] = self._registry.create(
                source_type, source_id, source_config
            )

    def create_source(self, source_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新数据源

        Args:
            source_type: 数据源类型
            config: 数据源配置

        Returns:
            数据源元信息字典
        """
        config = config or {}
        with self._lock:
            source = self._registry.create(source_type, config=config)
            self._sources[source.source_id] = source
            return source.to_dict()

    def get_source(self, source_id: str) -> Optional[BaseDataSource]:
        """获取数据源实例"""
        with self._lock:
            return self._sources.get(source_id)

    def list_sources(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有数据源

        Args:
            source_type: 可选，按类型过滤

        Returns:
            数据源元信息列表
        """
        with self._lock:
            sources = list(self._sources.values())
        if source_type:
            sources = [s for s in sources if s.source_type == source_type]
        return [s.to_dict() for s in sources]

    def remove_source(self, source_id: str) -> bool:
        """删除数据源

        默认数据源不可删除

        Args:
            source_id: 数据源ID

        Returns:
            是否成功删除
        """
        default_ids = {'api_default', 'websocket_default', 'file_stream_default', 'user_input_default'}
        if source_id in default_ids:
            return False
        with self._lock:
            return self._sources.pop(source_id, None) is not None

    def fetch_from_sources(self, source_ids: List[str], count_per_source: int = 10) -> List[Dict[str, Any]]:
        """从多个数据源获取设备数据并合并

        Args:
            source_ids: 数据源ID列表
            count_per_source: 每个数据源获取的条数

        Returns:
            合并后的设备数据列表
        """
        all_items = []
        for source_id in source_ids:
            source = self.get_source(source_id)
            if not source:
                continue
            mock_count = min(count_per_source, 20)
            equipment_data = source.get_equipment_data(mock_count)
            all_items.extend(equipment_data)
        return all_items

    @property
    def registry(self) -> DataSourceRegistry:
        """获取数据源注册表"""
        return self._registry
