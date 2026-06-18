"""
模拟数据源管理服务
提供设备/生产模拟数据源的注册、查询与生命周期管理（内存存储）
"""
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class DataSourceManager:
    """模拟数据源管理器（进程内单例存储）"""

    _sources: Dict[str, Dict[str, Any]] = {}
    _lock = threading.Lock()

    _DEFAULT_SOURCES = [
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

    def __init__(self):
        self._ensure_defaults()

    @classmethod
    def _ensure_defaults(cls):
        with cls._lock:
            if not cls._sources:
                for source in cls._DEFAULT_SOURCES:
                    cls._sources[source['source_id']] = dict(source)

    @classmethod
    def register_source(cls, source: Dict[str, Any]) -> Dict[str, Any]:
        """注册或更新数据源"""
        source_id = source.get('source_id')
        if not source_id:
            source_id = f"{source.get('type', 'unknown')}_{uuid.uuid4().hex[:8]}"
            source = {**source, 'source_id': source_id}

        entry = {
            'source_id': source_id,
            'type': source.get('type', 'unknown'),
            'name': source.get('name', f'数据源 {source_id}'),
            'description': source.get('description', ''),
            'status': source.get('status', 'active'),
            'config': source.get('config', {}),
            'created_at': source.get('created_at', datetime.now().isoformat()),
        }
        for key in ('endpoint', 'method', 'interval', 'url', 'file_path', 'format', 'form_config'):
            if key in source:
                entry[key] = source[key]

        with cls._lock:
            cls._sources[source_id] = entry
        return entry

    @classmethod
    def create_source(cls, source_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新数据源"""
        config = config or {}
        source_id = f"{source_type}_{uuid.uuid4().hex[:8]}"

        source = {
            'source_id': source_id,
            'type': source_type,
            'name': config.get('name', f'{source_type} 数据源'),
            'description': config.get('description', ''),
            'status': 'active',
            'config': config,
        }

        if source_type == 'api':
            source.update({
                'endpoint': config.get('endpoint', '/api/simulation/equipment/data'),
                'method': config.get('method', 'GET'),
                'interval': config.get('interval', 5),
                'description': config.get('description', '模拟API数据源，定期生成设备数据'),
            })
        elif source_type == 'websocket':
            source.update({
                'url': config.get('url', 'ws://localhost:5001/ws/equipment'),
                'interval': config.get('interval', 1),
                'description': config.get('description', '模拟WebSocket数据源，实时推送设备数据'),
            })
        elif source_type == 'file_stream':
            source.update({
                'file_path': config.get('file_path', ''),
                'format': config.get('format', 'csv'),
                'interval': config.get('interval', 10),
                'description': config.get('description', '模拟文件流数据源，从文件读取设备数据'),
            })
        elif source_type == 'user_input':
            source.update({
                'form_config': config.get('form_config', {}),
                'description': config.get('description', '模拟用户输入数据源'),
            })

        return cls.register_source(source)

    def list_sources(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有数据源"""
        self._ensure_defaults()
        with self._lock:
            sources = list(self._sources.values())
        if source_type:
            sources = [s for s in sources if s.get('type') == source_type]
        return sources

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """获取单个数据源"""
        self._ensure_defaults()
        with self._lock:
            return self._sources.get(source_id)

    def remove_source(self, source_id: str) -> bool:
        """删除数据源（默认数据源不可删除）"""
        default_ids = {s['source_id'] for s in self._DEFAULT_SOURCES}
        if source_id in default_ids:
            return False
        with self._lock:
            return self._sources.pop(source_id, None) is not None
