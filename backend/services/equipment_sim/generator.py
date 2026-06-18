"""
数据生成器层
纯函数化的设备数据生成逻辑
所有随机性通过 rng 参数注入，便于测试和复现
"""
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ============= 常量配置 =============

EQUIPMENT_STATUSES = ['running', 'idle', 'maintenance', 'error', 'offline']
STATUS_WEIGHTS = [0.5, 0.3, 0.1, 0.05, 0.05]

EQUIPMENT_TYPES = [
    '注塑机', '冲压机', '焊接机器人', '装配线', '包装机',
    '检测设备', '输送带', '切割机', '喷涂设备', '烘干炉'
]

MANUFACTURERS = ['厂商A', '厂商B', '厂商C', '厂商D', '厂商E']

MODEL_PREFIXES = ['MODEL-', 'TYPE-', 'VERSION-', 'GEN-']

SENSOR_TYPES = ['temperature', 'pressure', 'humidity', 'speed', 'vibration', 'current', 'voltage']

LOCATIONS = ['A车间', 'B车间', 'C车间', 'D车间', 'E车间', '中央仓库', '测试区']


# ============= 状态配置生成 =============

def get_status_parameters(status: str, rng: random.Random) -> Dict[str, Any]:
    """根据设备状态生成相关参数

    纯函数：给定相同的 status 和 rng 状态，输出相同

    Args:
        status: 设备状态
        rng: 随机数生成器实例

    Returns:
        状态相关参数字典
    """
    if status == 'running':
        return {
            'runtime_hours': round(rng.uniform(100, 10000), 2),
            'temperature': round(rng.uniform(25, 75), 2),
            'pressure': round(rng.uniform(20, 80), 2),
            'speed': round(rng.uniform(500, 2500), 2),
            'sensor_count': rng.randint(3, 8),
            'running_sensor_count_offset': 0,
            'warning_sensor_count_max': 2,
        }
    elif status == 'idle':
        return {
            'runtime_hours': round(rng.uniform(100, 5000), 2),
            'temperature': round(rng.uniform(20, 30), 2),
            'pressure': round(rng.uniform(0, 10), 2),
            'speed': 0,
            'sensor_count': rng.randint(2, 6),
            'running_sensor_count_offset': 0,
            'warning_sensor_count_max': 0,
        }
    elif status == 'maintenance':
        return {
            'runtime_hours': round(rng.uniform(500, 8000), 2),
            'temperature': round(rng.uniform(20, 40), 2),
            'pressure': round(rng.uniform(0, 20), 2),
            'speed': 0,
            'sensor_count': rng.randint(2, 5),
            'running_sensor_count_offset': -999,
            'warning_sensor_count_max': 0,
        }
    elif status == 'error':
        return {
            'runtime_hours': round(rng.uniform(1000, 5000), 2),
            'temperature': round(rng.uniform(60, 90), 2),
            'pressure': round(rng.uniform(70, 100), 2),
            'speed': round(rng.uniform(0, 100), 2),
            'sensor_count': rng.randint(1, 4),
            'running_sensor_count_offset': -999,
            'warning_sensor_count_max': 0,
        }
    else:  # offline
        return {
            'runtime_hours': round(rng.uniform(0, 3000), 2),
            'temperature': round(rng.uniform(15, 25), 2),
            'pressure': round(rng.uniform(0, 5), 2),
            'speed': 0,
            'sensor_count': rng.randint(0, 3),
            'running_sensor_count_offset': -999,
            'warning_sensor_count_max': -999,
        }


def _compute_sensor_counts(status_params: Dict[str, Any], rng: random.Random) -> Tuple[int, int, int]:
    """计算运行中、告警中的传感器数量

    Args:
        status_params: 状态参数
        rng: 随机数生成器

    Returns:
        (sensor_count, running_sensor_count, warning_sensor_count)
    """
    sensor_count = status_params['sensor_count']
    offset = status_params['running_sensor_count_offset']
    warn_max = status_params['warning_sensor_count_max']

    if offset == -999:
        running_sensor_count = 0
    else:
        running_sensor_count = sensor_count - rng.randint(0, min(2, sensor_count))

    if warn_max == -999:
        warning_sensor_count = 0
    else:
        warning_sensor_count = min(
            sensor_count - running_sensor_count,
            rng.randint(0, warn_max)
        )
        if warning_sensor_count < 0:
            warning_sensor_count = 0

    return sensor_count, running_sensor_count, warning_sensor_count


# ============= 单条设备数据生成 =============

def generate_single_equipment(
    index: int,
    rng: random.Random,
    line_id: Optional[int] = None,
    status: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """生成单条设备模拟数据

    纯函数：给定相同参数（含相同 rng 状态），输出完全相同

    Args:
        index: 设备索引（用于生成ID）
        rng: 随机数生成器实例
        line_id: 可选，指定生产线ID
        status: 可选，指定设备状态
        now: 可选，指定当前时间

    Returns:
        设备数据字典
    """
    now = now or datetime.now()

    equipment_status = status if status else rng.choices(
        EQUIPMENT_STATUSES, weights=STATUS_WEIGHTS
    )[0]

    status_params = get_status_parameters(equipment_status, rng)
    sensor_count, running_sensor_count, warning_sensor_count = _compute_sensor_counts(
        status_params, rng
    )

    equipment_line_id = line_id if line_id else rng.randint(1, 5)

    return {
        'id': index + 1,
        'equipment_code': f'EQP-{1000 + index}',
        'equipment_name': f'{rng.choice(EQUIPMENT_TYPES)}-{index + 1}',
        'equipment_type': rng.choice(EQUIPMENT_TYPES),
        'line_id': equipment_line_id,
        'line_name': f'生产线{equipment_line_id}',
        'status': equipment_status,
        'model': f'{rng.choice(MODEL_PREFIXES)}{rng.randint(100, 999)}',
        'manufacturer': rng.choice(MANUFACTURERS),
        'purchase_date': (now - timedelta(days=rng.randint(100, 1000))).strftime('%Y-%m-%d'),
        'install_date': (now - timedelta(days=rng.randint(50, 500))).strftime('%Y-%m-%d'),
        'runtime_hours': status_params['runtime_hours'],
        'temperature': status_params['temperature'],
        'pressure': status_params['pressure'],
        'speed': status_params['speed'],
        'sensor_count': sensor_count,
        'running_sensor_count': running_sensor_count,
        'warning_sensor_count': warning_sensor_count,
        'location': rng.choice(LOCATIONS),
        'last_maintenance': (now - timedelta(days=rng.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S'),
        'next_maintenance': (now + timedelta(days=rng.randint(1, 90))).strftime('%Y-%m-%d %H:%M:%S'),
        'create_time': (now - timedelta(days=rng.randint(1, 365))).strftime('%Y-%m-%d %H:%M:%S'),
        'update_time': now.strftime('%Y-%m-%d %H:%M:%S'),
    }


# ============= 批量设备数据生成 =============

def generate_equipment_batch(
    total: int,
    rng: random.Random,
    line_id: Optional[int] = None,
    status: Optional[str] = None,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """生成批量设备数据

    纯函数：给定相同参数（含相同 rng 状态），输出完全相同

    Args:
        total: 生成总数
        rng: 随机数生成器实例
        line_id: 可选，指定生产线ID
        status: 可选，指定设备状态
        now: 可选，指定当前时间

    Returns:
        设备数据列表
    """
    return [
        generate_single_equipment(i, rng, line_id, status, now)
        for i in range(total)
    ]


# ============= 分页数据生成 =============

def generate_paginated_equipment(
    page: int,
    size: int,
    rng: random.Random,
    line_id: Optional[int] = None,
    status: Optional[str] = None,
    total_range: Optional[Tuple[int, int]] = None,
    now: Optional[datetime] = None,
) -> Tuple[Dict[str, Any], int]:
    """生成分页设备数据

    纯函数：给定相同参数（含相同 rng 状态），输出完全相同

    Args:
        page: 页码
        size: 每页大小
        rng: 随机数生成器实例
        line_id: 可选，指定生产线ID
        status: 可选，指定设备状态
        total_range: 可选，总数范围 (min, max)
        now: 可选，指定当前时间

    Returns:
        (分页数据字典, 总数)
    """
    total_range = total_range or (50, 200)
    total = rng.randint(*total_range)

    start_idx = (page - 1) * size
    end_idx = min(start_idx + size, total)

    items = []
    for i in range(start_idx, end_idx):
        items.append(generate_single_equipment(i, rng, line_id, status, now))

    data = {
        'items': items,
        'total': total,
        'page': page,
        'size': size,
        'pages': (total + size - 1) // size if size > 0 else 0,
    }
    return data, total


# ============= 配置信息 =============

def get_simulation_config() -> Dict[str, Any]:
    """获取设备模拟配置

    纯函数：无状态

    Returns:
        配置字典
    """
    return {
        'data_sources': {
            'enabled': True,
            'max_sources': 5,
            'default_sources': ['api', 'websocket']
        },
        'pagination': {
            'default_page': 1,
            'default_size': 10,
            'max_size': 100
        },
        'refresh': {
            'auto_refresh': False,
            'refresh_interval': 30,
            'manual_refresh': True
        },
        'data_generation': {
            'total_range': [50, 200],
            'status_distribution': dict(zip(EQUIPMENT_STATUSES, STATUS_WEIGHTS)),
            'sensor_range': [1, 8],
            'runtime_range': [0, 10000]
        }
    }


# ============= 数据源数据分页包装 =============

def paginate_items(
    items: List[Dict[str, Any]],
    page: int,
    size: int,
) -> Dict[str, Any]:
    """对已有数据列表进行分页包装

    纯函数

    Args:
        items: 数据项列表
        page: 页码
        size: 每页大小

    Returns:
        分页数据字典
    """
    total = len(items)
    start = (page - 1) * size
    page_items = items[start:start + size]

    return {
        'items': page_items,
        'total': total,
        'page': page,
        'size': size,
        'pages': (total + size - 1) // size if size > 0 else 0,
    }
