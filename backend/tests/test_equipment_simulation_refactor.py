"""
设备模拟服务重构单元测试
验证重构后的分层架构与原实现的等价性
"""
import sys
import os
import random
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestGeneratorPureFunctions:
    """测试 Generator 层的纯函数特性"""

    def test_generate_single_equipment_deterministic(self):
        """测试单条设备数据生成的确定性：相同 seed 产生相同输出"""
        from services.equipment_sim.generator import generate_single_equipment

        rng1 = random.Random(42)
        rng2 = random.Random(42)

        result1 = generate_single_equipment(0, rng1)
        result2 = generate_single_equipment(0, rng2)

        assert result1 == result2
        assert result1['id'] == 1
        assert result1['equipment_code'] == 'EQP-1000'

    def test_generate_paginated_equipment_structure(self):
        """测试分页数据生成的结构正确性"""
        from services.equipment_sim.generator import generate_paginated_equipment

        rng = random.Random(123)
        data, total = generate_paginated_equipment(page=1, size=10, rng=rng)

        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'size' in data
        assert 'pages' in data
        assert len(data['items']) == 10
        assert data['total'] == total
        assert data['page'] == 1
        assert data['size'] == 10

    def test_generate_equipment_with_status_filter(self):
        """测试指定状态筛选时，所有设备都为指定状态"""
        from services.equipment_sim.generator import generate_equipment_batch

        rng = random.Random(456)
        items = generate_equipment_batch(total=20, rng=rng, status='running')

        assert len(items) == 20
        for item in items:
            assert item['status'] == 'running'
            assert item['speed'] > 0

    def test_generate_equipment_with_line_id(self):
        """测试指定生产线ID时，所有设备都属于该生产线"""
        from services.equipment_sim.generator import generate_equipment_batch

        rng = random.Random(789)
        items = generate_equipment_batch(total=15, rng=rng, line_id=3)

        assert len(items) == 15
        for item in items:
            assert item['line_id'] == 3
            assert item['line_name'] == '生产线3'

    def test_status_parameters_consistency(self):
        """测试各状态参数的一致性"""
        from services.equipment_sim.generator import get_status_parameters, EQUIPMENT_STATUSES

        rng = random.Random(999)
        for status in EQUIPMENT_STATUSES:
            params = get_status_parameters(status, rng)
            assert 'runtime_hours' in params
            assert 'temperature' in params
            assert 'pressure' in params
            assert 'speed' in params
            assert 'sensor_count' in params

    def test_paginate_items_correctness(self):
        """测试分页包装函数的正确性"""
        from services.equipment_sim.generator import paginate_items

        items = [{'id': i} for i in range(25)]

        page1 = paginate_items(items, page=1, size=10)
        assert len(page1['items']) == 10
        assert page1['items'][0]['id'] == 0
        assert page1['total'] == 25
        assert page1['pages'] == 3

        page3 = paginate_items(items, page=3, size=10)
        assert len(page3['items']) == 5
        assert page3['items'][0]['id'] == 20

    def test_get_simulation_config_structure(self):
        """测试配置获取函数的结构"""
        from services.equipment_sim.generator import get_simulation_config

        config = get_simulation_config()

        assert 'data_sources' in config
        assert 'pagination' in config
        assert 'refresh' in config
        assert 'data_generation' in config
        assert config['pagination']['default_page'] == 1
        assert config['pagination']['default_size'] == 10


class TestDataSourceLayer:
    """测试 DataSource 层的架构"""

    def test_base_data_source_is_abstract(self):
        """测试 BaseDataSource 是抽象基类，不能直接实例化"""
        from services.equipment_sim.data_sources import BaseDataSource

        with pytest.raises(TypeError):
            BaseDataSource('test_id', {})

    def test_api_data_source_fetch_and_convert(self):
        """测试 API 数据源的获取和转换功能"""
        from services.equipment_sim.data_sources import ApiDataSource

        source = ApiDataSource('api_test_001', {'name': '测试API源'})

        raw_data = source.fetch_data(count=5)
        assert len(raw_data) == 5
        for item in raw_data:
            assert 'value' in item
            assert 'source_id' in item

        converted = source.convert(raw_data)
        assert len(converted) == 5
        for eq in converted:
            assert 'equipment_code' in eq
            assert 'equipment_name' in eq
            assert eq['equipment_type'] == 'API设备'

    def test_all_default_data_source_types(self):
        """测试所有默认数据源类型都能正确实例化并生成数据"""
        from services.equipment_sim.data_sources import DataSourceRegistry

        registry = DataSourceRegistry()
        source_types = registry.list_types()

        assert len(source_types) >= 4
        assert 'api' in source_types
        assert 'websocket' in source_types
        assert 'file_stream' in source_types
        assert 'user_input' in source_types

        for source_type in source_types:
            source = registry.create(source_type, source_id=f'test_{source_type}')
            data = source.get_equipment_data(count=3)
            assert len(data) == 3
            assert source.source_type == source_type

    def test_data_source_registry_register_new_type(self):
        """测试新增数据源只需注册子类（开闭原则验证）"""
        from services.equipment_sim.data_sources import BaseDataSource, DataSourceRegistry

        class CustomDataSource(BaseDataSource):
            source_type = "custom"

            def fetch_data(self, count=10):
                return [{'custom_value': i} for i in range(count)]

            def convert(self, raw_data):
                return [
                    {
                        'id': i,
                        'equipment_code': f'CUSTOM-{i}',
                        'equipment_name': f'自定义设备{i}',
                        'equipment_type': '自定义类型',
                        'status': 'running',
                    }
                    for i, _ in enumerate(raw_data)
                ]

        registry = DataSourceRegistry()
        registry.register('custom', CustomDataSource)

        assert registry.has_type('custom')
        source = registry.create('custom', source_id='custom_test')
        assert source.source_type == 'custom'

        data = source.get_equipment_data(count=3)
        assert len(data) == 3
        assert data[0]['equipment_type'] == '自定义类型'

    def test_data_source_manager_default_sources(self):
        """测试数据源管理器初始化时有默认数据源"""
        from services.equipment_sim.data_sources import DataSourceManager

        manager = DataSourceManager()
        sources = manager.list_sources()

        assert len(sources) == 4
        source_ids = [s['source_id'] for s in sources]
        assert 'api_default' in source_ids
        assert 'websocket_default' in source_ids
        assert 'file_stream_default' in source_ids
        assert 'user_input_default' in source_ids

    def test_data_source_manager_create_and_remove(self):
        """测试创建和删除数据源"""
        from services.equipment_sim.data_sources import DataSourceManager

        manager = DataSourceManager()
        initial_count = len(manager.list_sources())

        result = manager.create_source('api', {'name': '新API源'})
        assert 'source_id' in result
        assert result['type'] == 'api'

        new_count = len(manager.list_sources())
        assert new_count == initial_count + 1

        removed = manager.remove_source(result['source_id'])
        assert removed is True

        final_count = len(manager.list_sources())
        assert final_count == initial_count

    def test_data_source_manager_cannot_remove_default(self):
        """测试默认数据源不可删除"""
        from services.equipment_sim.data_sources import DataSourceManager

        manager = DataSourceManager()
        result = manager.remove_source('api_default')
        assert result is False

    def test_fetch_from_multiple_sources(self):
        """测试从多个数据源获取数据"""
        from services.equipment_sim.data_sources import DataSourceManager

        manager = DataSourceManager()
        data = manager.fetch_from_sources(
            ['api_default', 'websocket_default'],
            count_per_source=5
        )

        assert len(data) == 10


class TestScheduler:
    """测试 Scheduler 调度层"""

    def test_scheduler_initial_state(self):
        """测试调度器初始状态为未运行"""
        from services.equipment_sim.scheduler import RefreshScheduler

        scheduler = RefreshScheduler()
        assert scheduler.is_running is False
        assert scheduler.interval == 30

    def test_scheduler_start_and_stop(self):
        """测试调度器的启动和停止功能"""
        from services.equipment_sim.scheduler import RefreshScheduler

        scheduler = RefreshScheduler()
        call_count = [0]
        event = threading.Event()

        def callback():
            call_count[0] += 1
            event.set()

        started = scheduler.start(interval=1, callback=callback)
        assert started is True
        assert scheduler.is_running is True

        assert event.wait(timeout=3), "回调函数未被调用"
        assert call_count[0] >= 1

        stopped = scheduler.stop()
        assert stopped is True
        assert scheduler.is_running is False

    def test_scheduler_start_twice_returns_false(self):
        """测试重复启动返回 False"""
        from services.equipment_sim.scheduler import RefreshScheduler

        scheduler = RefreshScheduler()
        r1 = scheduler.start(interval=1)
        r2 = scheduler.start(interval=1)

        assert r1 is True
        assert r2 is False

        scheduler.stop()

    def test_scheduler_stop_when_not_running(self):
        """测试未运行时停止返回 False"""
        from services.equipment_sim.scheduler import RefreshScheduler

        scheduler = RefreshScheduler()
        result = scheduler.stop()
        assert result is False

    def test_scheduler_get_status(self):
        """测试获取调度器状态"""
        from services.equipment_sim.scheduler import RefreshScheduler

        scheduler = RefreshScheduler()
        status = scheduler.get_status()

        assert status['is_running'] is False
        assert status['interval'] == 30
        assert status['has_callback'] is False


class TestSideEffectDispatcher:
    """测试 SideEffectDispatcher 副作用派发层"""

    def test_dispatcher_register_and_dispatch(self):
        """测试注册和派发副作用处理器"""
        from services.equipment_sim.side_effects import SideEffectDispatcher

        dispatcher = SideEffectDispatcher()
        results = []

        def test_handler(value):
            results.append(value)
            return value * 2

        dispatcher.register_handler('test', test_handler)
        assert dispatcher.has_handler('test')

        result = dispatcher.dispatch('test', 42)
        assert result == 84
        assert len(results) == 1
        assert results[0] == 42

    def test_dispatcher_dispatch_unknown_handler(self):
        """测试派发不存在的处理器返回 None"""
        from services.equipment_sim.side_effects import SideEffectDispatcher

        dispatcher = SideEffectDispatcher()
        result = dispatcher.dispatch('nonexistent', 'data')
        assert result is None

    def test_dispatcher_disabled(self):
        """测试禁用后派发不执行"""
        from services.equipment_sim.side_effects import SideEffectDispatcher

        dispatcher = SideEffectDispatcher()
        call_count = [0]

        def handler():
            call_count[0] += 1

        dispatcher.register_handler('count', handler)
        dispatcher.set_enabled(False)

        dispatcher.dispatch('count')
        assert call_count[0] == 0

        dispatcher.set_enabled(True)
        dispatcher.dispatch('count')
        assert call_count[0] == 1

    def test_dispatcher_unregister(self):
        """测试取消注册处理器"""
        from services.equipment_sim.side_effects import SideEffectDispatcher

        dispatcher = SideEffectDispatcher()
        dispatcher.register_handler('test', lambda x: x)
        assert dispatcher.has_handler('test')

        result = dispatcher.unregister_handler('test')
        assert result is True
        assert not dispatcher.has_handler('test')

        result2 = dispatcher.unregister_handler('nonexistent')
        assert result2 is False

    def test_dispatcher_list_handlers(self):
        """测试列出所有处理器"""
        from services.equipment_sim.side_effects import SideEffectDispatcher

        dispatcher = SideEffectDispatcher()
        dispatcher.register_handler('a', lambda: None)
        dispatcher.register_handler('b', lambda: None)

        handlers = dispatcher.list_handlers()
        assert len(handlers) == 2
        assert 'a' in handlers
        assert 'b' in handlers


class TestServiceApiCompatibility:
    """测试主服务 API 兼容性（与原实现等价）"""

    def test_equipment_simulation_service_class_exists(self):
        """测试 EquipmentSimulationService 类存在且有所有静态方法"""
        from services.equipment_simulation_service import EquipmentSimulationService

        assert hasattr(EquipmentSimulationService, 'generate_equipment_simulation_data')
        assert hasattr(EquipmentSimulationService, 'get_equipment_simulation_config')
        assert hasattr(EquipmentSimulationService, 'start_auto_refresh')
        assert hasattr(EquipmentSimulationService, 'create_mock_equipment_data_source')

    def test_class_constants_are_preserved(self):
        """测试类常量保持不变"""
        from services.equipment_simulation_service import EquipmentSimulationService

        assert hasattr(EquipmentSimulationService, 'EQUIPMENT_STATUSES')
        assert hasattr(EquipmentSimulationService, 'STATUS_WEIGHTS')
        assert hasattr(EquipmentSimulationService, 'EQUIPMENT_TYPES')
        assert hasattr(EquipmentSimulationService, 'MANUFACTURERS')

        assert len(EquipmentSimulationService.EQUIPMENT_STATUSES) == 5
        assert 'running' in EquipmentSimulationService.EQUIPMENT_STATUSES
        assert 'offline' in EquipmentSimulationService.EQUIPMENT_STATUSES

    def test_generate_equipment_simulation_data_returns_tuple(self):
        """测试生成数据返回 (dict, int) 格式"""
        from services.equipment_simulation_service import EquipmentSimulationService

        data, total = EquipmentSimulationService.generate_equipment_simulation_data(
            page=1, size=10
        )

        assert isinstance(data, dict)
        assert isinstance(total, int)
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'size' in data
        assert data['total'] == total

    def test_get_equipment_simulation_config_returns_dict(self):
        """测试获取配置返回字典"""
        from services.equipment_simulation_service import EquipmentSimulationService

        config = EquipmentSimulationService.get_equipment_simulation_config()

        assert isinstance(config, dict)
        assert 'data_sources' in config
        assert 'pagination' in config
        assert 'refresh' in config
        assert 'data_generation' in config

    def test_start_auto_refresh_returns_thread(self):
        """测试启动自动刷新返回线程对象"""
        from services.equipment_simulation_service import EquipmentSimulationService

        thread = EquipmentSimulationService.start_auto_refresh(interval=1)

        assert thread is not None
        assert isinstance(thread, threading.Thread)
        assert thread.is_alive()

        time.sleep(0.5)

    def test_create_mock_equipment_data_source(self):
        """测试创建设备模拟数据源"""
        from services.equipment_simulation_service import EquipmentSimulationService
        from services.equipment_sim.service import EquipmentSimulationService as _ServiceImpl

        _ServiceImpl._reset_instance()

        result = EquipmentSimulationService.create_mock_equipment_data_source(
            'api',
            {'name': '测试数据源'}
        )

        assert isinstance(result, dict)
        assert 'source_id' in result
        assert 'type' in result
        assert 'status' in result
        assert result['type'] == 'api'
        assert result['status'] == 'created'

    def test_service_instance_independence(self):
        """测试不同服务实例之间状态独立（消除全局可变状态）"""
        from services.equipment_sim.service import EquipmentSimulationService

        service1 = EquipmentSimulationService()
        service2 = EquipmentSimulationService()

        service1.create_mock_equipment_data_source('api', {'name': '源1'})
        sources1 = service1.data_source_manager.list_sources()
        sources2 = service2.data_source_manager.list_sources()

        assert len(sources1) == len(sources2) + 1

        service1.start_auto_refresh(interval=60)
        assert service1.scheduler.is_running is True
        assert service2.scheduler.is_running is False

        service1.stop_auto_refresh()

    def test_no_circular_imports(self):
        """测试无循环导入（通过验证各模块可独立导入）"""
        import importlib

        modules = [
            'services.equipment_sim.data_sources',
            'services.equipment_sim.generator',
            'services.equipment_sim.scheduler',
            'services.equipment_sim.side_effects',
            'services.equipment_sim.service',
            'services.equipment_sim.__init__',
        ]

        for module_name in modules:
            if module_name in sys.modules:
                del sys.modules[module_name]

        for module_name in modules:
            module = importlib.import_module(module_name)
            assert module is not None

    def test_new_data_source_extensibility(self):
        """测试新增数据源的扩展性：只需新增子类 + 注册"""
        from services.equipment_sim.data_sources import (
            BaseDataSource, DataSourceRegistry, DataSourceManager
        )
        from services.equipment_sim.service import EquipmentSimulationService

        class MqttDataSource(BaseDataSource):
            source_type = "mqtt"

            def fetch_data(self, count=10):
                return [{'topic': f'sensor/{i}', 'value': i * 1.5} for i in range(count)]

            def convert(self, raw_data):
                return [
                    {
                        'id': i + 6000,
                        'equipment_code': f'MQTT-EQP-{i}',
                        'equipment_name': f'MQTT设备{i}',
                        'equipment_type': 'MQTT设备',
                        'line_id': 1,
                        'line_name': '生产线1',
                        'status': 'running',
                        'model': 'MQTT-MODEL',
                        'manufacturer': 'MQTT厂商',
                        'runtime_hours': float(item['value']),
                        'temperature': 25.0,
                        'pressure': 50.0,
                        'speed': 1000.0,
                        'sensor_count': 4,
                        'running_sensor_count': 4,
                        'warning_sensor_count': 0,
                        'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    for i, item in enumerate(raw_data)
                ]

        service = EquipmentSimulationService()
        service.data_source_manager.registry.register('mqtt', MqttDataSource)

        result = service.create_mock_equipment_data_source('mqtt', {'name': 'MQTT数据源'})
        assert result['status'] == 'created'

        source = service.data_source_manager.get_source(result['source_id'])
        assert source is not None
        assert source.source_type == 'mqtt'

        data = source.get_equipment_data(count=3)
        assert len(data) == 3
        assert data[0]['equipment_type'] == 'MQTT设备'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
