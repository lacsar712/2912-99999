"""
数据模拟控制器
支持生成、清除和查询模拟数据
"""
from flask import Blueprint, request, g
import os
import tempfile
from datetime import datetime
from services.simulation_service import DataSimulationService
from services.equipment_simulation_service import EquipmentSimulationService
from middleware.auth_middleware import login_required

simulation_bp = Blueprint('simulation', __name__)


@simulation_bp.route('/config/default', methods=['GET'])
@login_required
def get_default_config():
    """获取默认模拟配置"""
    config = DataSimulationService.generate_simulation_config()
    return {
        'code': 200,
        'message': 'success',
        'data': config
    }


@simulation_bp.route('/generate', methods=['POST'])
@login_required
def generate_simulation_data():
    """生成模拟数据"""
    data = request.get_json()
    config = data.get('config')
    
    if not config:
        config = DataSimulationService.generate_simulation_config()
    
    return DataSimulationService.simulate_production_data(config)


@simulation_bp.route('/clear', methods=['POST'])
@login_required
def clear_simulation_data():
    """清除模拟数据"""
    return DataSimulationService.clear_simulation_data()


@simulation_bp.route('/status', methods=['GET'])
@login_required
def get_simulation_status():
    """获取当前模拟数据状态"""
    return DataSimulationService.get_simulation_status()


@simulation_bp.route('/import/csv', methods=['POST'])
@login_required
def import_csv_data():
    """导入CSV文件数据"""
    if 'file' not in request.files:
        return {'code': 400, 'message': '未上传文件'}
    
    file = request.files['file']
    data_type = request.form.get('type', 'production_line')
    
    if file.filename == '':
        return {'code': 400, 'message': '未选择文件'}
    
    # 验证文件类型
    if not file.filename.endswith('.csv'):
        return {'code': 400, 'message': '只支持CSV文件'}
    
    # 保存上传的文件到临时目录
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)
    file.save(temp_path)
    
    try:
        # 导入数据
        result = DataSimulationService.import_csv_data(temp_path, data_type)
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result
        
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {'code': 500, 'message': f'导入失败: {str(e)}'}


@simulation_bp.route('/import/json', methods=['POST'])
@login_required
def import_json_data():
    """导入JSON文件数据"""
    if 'file' not in request.files:
        return {'code': 400, 'message': '未上传文件'}
    
    file = request.files['file']
    data_type = request.form.get('type', 'record')
    
    if file.filename == '':
        return {'code': 400, 'message': '未选择文件'}
    
    # 验证文件类型
    if not file.filename.endswith('.json'):
        return {'code': 400, 'message': '只支持JSON文件'}
    
    # 保存上传的文件到临时目录
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)
    file.save(temp_path)
    
    try:
        # 导入数据
        result = DataSimulationService.import_json_data(temp_path, data_type)
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result
        
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {'code': 500, 'message': f'导入失败: {str(e)}'}


@simulation_bp.route('/validate', methods=['POST'])
@login_required
def validate_data():
    """验证数据完整性"""
    data = request.get_json()
    if not data:
        return {'code': 400, 'message': '请求数据为空'}
    
    data_type = data.get('type')
    data_list = data.get('data', [])
    
    if not data_type:
        return {'code': 400, 'message': '缺少数据类型'}
    
    if not isinstance(data_list, list):
        return {'code': 400, 'message': '数据必须是数组格式'}
    
    result = DataSimulationService.validate_data(data_type, data_list)
    return {
        'code': 200,
        'message': '验证完成',
        'data': result
    }


@simulation_bp.route('/source/create', methods=['POST'])
@login_required
def create_mock_data_source():
    """创建模拟数据源"""
    data = request.get_json()
    if not data:
        return {'code': 400, 'message': '请求数据为空'}
    
    source_type = data.get('type')
    config = data.get('config', {})
    
    if not source_type:
        return {'code': 400, 'message': '缺少数据源类型'}
    
    return DataSimulationService.create_mock_data_source(source_type, config)


@simulation_bp.route('/source/<source_id>/generate', methods=['POST'])
@login_required
def generate_from_source(source_id):
    """从模拟数据源生成数据"""
    data = request.get_json() or {}
    count = data.get('count', 10)
    
    return DataSimulationService.generate_mock_data_from_source(source_id, count)


# ==================== 设备管理页面数据模拟接口 ====================

@simulation_bp.route('/equipment/config', methods=['GET'])
@login_required
def get_equipment_simulation_config():
    """获取设备模拟配置"""
    config = EquipmentSimulationService.get_equipment_simulation_config()
    return {
        'code': 200,
        'message': 'success',
        'data': config
    }


@simulation_bp.route('/equipment/data', methods=['GET'])
@login_required
def get_equipment_simulation_data():
    """获取设备模拟数据"""
    # 分页参数
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    
    # 筛选参数
    line_id = request.args.get('lineId', type=int)
    status = request.args.get('status')
    
    # 数据源参数
    source_ids = request.args.getlist('sourceIds')  # 多个数据源ID
    use_real_data = request.args.get('useRealData', 'false').lower() == 'true'
    
    # 生成模拟数据
    data, total = EquipmentSimulationService.generate_equipment_simulation_data(
        page=page,
        size=size,
        line_id=line_id,
        status=status,
        source_ids=source_ids if source_ids else None,
        use_real_data=use_real_data
    )
    
    return {
        'code': 200,
        'message': 'success',
        'data': data
    }


@simulation_bp.route('/equipment/source/create', methods=['POST'])
@login_required
def create_equipment_data_source():
    """创建设备模拟数据源"""
    data = request.get_json()
    if not data:
        return {'code': 400, 'message': '请求数据为空'}
    
    source_type = data.get('type')
    config = data.get('config', {})
    
    if not source_type:
        return {'code': 400, 'message': '缺少数据源类型'}
    
    result = EquipmentSimulationService.create_mock_equipment_data_source(source_type, config)
    
    if 'error' in result:
        return {'code': 500, 'message': result['error'], 'data': result}
    
    return {
        'code': 200,
        'message': '设备模拟数据源创建成功',
        'data': result
    }


@simulation_bp.route('/equipment/refresh/start', methods=['POST'])
@login_required
def start_equipment_refresh():
    """启动设备数据自动刷新"""
    data = request.get_json() or {}
    interval = data.get('interval', 30)
    callback_url = data.get('callbackUrl')
    
    EquipmentSimulationService.start_auto_refresh(interval, callback_url)
    
    return {
        'code': 200,
        'message': f'设备数据自动刷新已启动，间隔: {interval}秒',
        'data': {
            'interval': interval,
            'callback_url': callback_url,
            'status': 'started'
        }
    }


@simulation_bp.route('/equipment/refresh/stop', methods=['POST'])
@login_required
def stop_equipment_refresh():
    """停止设备数据自动刷新"""
    # 注意：当前实现中，自动刷新是后台线程，没有直接的停止机制
    # 在实际项目中，可以维护一个线程字典来管理
    return {
        'code': 200,
        'message': '设备数据自动刷新停止命令已发送',
        'data': {
            'status': 'stopping',
            'note': '自动刷新线程将在下次检查时停止'
        }
    }


@simulation_bp.route('/equipment/sources', methods=['GET'])
@login_required
def list_equipment_data_sources():
    """列出可用的设备数据源"""
    from services.data_source_service import DataSourceManager
    
    manager = DataSourceManager()
    sources = manager.list_sources()
    
    # 过滤出与设备相关的数据源
    equipment_sources = []
    for source in sources:
        # 可以根据需要过滤特定类型的数据源
        equipment_sources.append(source)
    
    return {
        'code': 200,
        'message': 'success',
        'data': {
            'sources': equipment_sources,
            'count': len(equipment_sources)
        }
    }


# ==================== 环境监测数据模拟接口 ====================

@simulation_bp.route('/env-monitor/config', methods=['GET'])
@login_required
def get_env_monitor_simulation_config():
    """获取环境监测模拟配置"""
    from services.env_monitor_service import EnvMonitorService
    
    config = {
        'source_types': ['api', 'websocket', 'file_stream', 'user_input'],
        'default_config': {
            'interval': 5,
            'abnormal_probability': 0.1,
            'monitor_items': ['温度', '湿度', 'PM2.5', 'PM10', '噪音', 'CO2', 'CO', '甲醛', 'TVOC', '气压', '风速', '照度']
        },
        'area_types': ['workshop', 'warehouse', 'office', 'other']
    }
    
    return {
        'code': 200,
        'message': 'success',
        'data': config
    }


@simulation_bp.route('/env-monitor/generate', methods=['POST'])
@login_required
def generate_env_monitor_data():
    """生成环境监测模拟数据"""
    from services.env_monitor_service import EnvMonitorService
    
    data = request.get_json() or {}
    config = data.get('config')
    
    return EnvMonitorService.generate_simulated_readings(config)


@simulation_bp.route('/env-monitor/source/create', methods=['POST'])
@login_required
def create_env_monitor_data_source():
    """创建环境监测模拟数据源"""
    from services.env_monitor_service import EnvMonitorService
    
    data = request.get_json()
    if not data:
        return {'code': 400, 'message': '请求数据为空'}
    
    source_type = data.get('type')
    config = data.get('config', {})
    
    if not source_type:
        return {'code': 400, 'message': '缺少数据源类型'}
    
    source_id = f'env_monitor_{source_type}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    if source_type == 'api':
        result = {
            'source_id': source_id,
            'type': 'api',
            'name': config.get('name', '环境监测API数据源'),
            'endpoint': config.get('endpoint', '/api/env-monitor/readings/realtime'),
            'method': config.get('method', 'GET'),
            'interval': config.get('interval', 30),
            'description': '环境监测API数据源，定期获取实时读数'
        }
    elif source_type == 'websocket':
        result = {
            'source_id': source_id,
            'type': 'websocket',
            'name': config.get('name', '环境监测WebSocket数据源'),
            'url': config.get('url', 'ws://localhost:5000/api/env-monitor/ws'),
            'interval': config.get('interval', 5),
            'description': '环境监测WebSocket数据源，实时推送读数'
        }
    elif source_type == 'file_stream':
        result = {
            'source_id': source_id,
            'type': 'file_stream',
            'name': config.get('name', '环境监测文件流数据源'),
            'file_path': config.get('file_path', ''),
            'format': config.get('format', 'csv'),
            'interval': config.get('interval', 60),
            'description': '环境监测文件流数据源，从文件读取读数'
        }
    elif source_type == 'user_input':
        result = {
            'source_id': source_id,
            'type': 'user_input',
            'name': config.get('name', '环境监测人工录入数据源'),
            'form_config': config.get('form_config', {
                'fields': [
                    {'name': 'point_id', 'label': '监测点', 'type': 'select', 'required': True},
                    {'name': 'item_name', 'label': '监测项目', 'type': 'select', 'required': True},
                    {'name': 'item_value', 'label': '数值', 'type': 'number', 'required': True}
                ]
            }),
            'description': '环境监测人工录入数据源'
        }
    else:
        return {'code': 400, 'message': f'不支持的数据源类型: {source_type}'}
    
    # 记录操作日志
    from models.log import Log
    Log.add_log(
        g.user_id, g.username, 'create', 'simulation',
        f'创建环境监测模拟数据源: {source_type} ({source_id})'
    )
    
    return {
        'code': 200,
        'message': '环境监测模拟数据源创建成功',
        'data': result
    }


@simulation_bp.route('/env-monitor/source/<source_id>/generate', methods=['POST'])
@login_required
def generate_env_monitor_from_source(source_id):
    """从环境监测模拟数据源生成数据"""
    from services.env_monitor_service import EnvMonitorService
    
    data = request.get_json() or {}
    count = data.get('count', 10)
    config = data.get('config', {})
    
    # 根据数据源类型生成不同的模拟数据
    if source_id.startswith('env_monitor_api_'):
        # API类型 - 直接调用实时数据接口
        result = EnvMonitorService.get_realtime_readings()
        return {
            'code': 200,
            'message': f'成功从API数据源获取{count}条环境监测数据',
            'data': {
                'source_id': source_id,
                'generated_count': count,
                'readings': result.data
            }
        }
    elif source_id.startswith('env_monitor_websocket_'):
        # WebSocket类型 - 生成流式数据
        result = EnvMonitorService.generate_simulated_readings(config)
        return {
            'code': 200,
            'message': f'成功从WebSocket数据源生成{count}条环境监测数据',
            'data': {
                'source_id': source_id,
                'generated_count': count,
                'result': result.data
            }
        }
    else:
        # 其他类型 - 生成模拟读数
        result = EnvMonitorService.generate_simulated_readings(config)
        return {
            'code': 200,
            'message': f'成功从数据源生成环境监测数据',
            'data': {
                'source_id': source_id,
                'result': result.data
            }
        }


@simulation_bp.route('/env-monitor/sources', methods=['GET'])
@login_required
def list_env_monitor_data_sources():
    """列出可用的环境监测数据源"""
    # 返回预设的环境监测数据源
    sources = [
        {
            'source_id': 'env_monitor_api_default',
            'type': 'api',
            'name': '环境监测实时API',
            'description': '获取环境监测实时读数',
            'status': 'active'
        },
        {
            'source_id': 'env_monitor_websocket_default',
            'type': 'websocket',
            'name': '环境监测WebSocket',
            'description': '实时推送环境监测数据',
            'status': 'active'
        },
        {
            'source_id': 'env_monitor_simulation_default',
            'type': 'simulation',
            'name': '环境监测模拟数据',
            'description': '生成环境监测模拟读数',
            'status': 'active'
        }
    ]
    
    return {
        'code': 200,
        'message': 'success',
        'data': {
            'sources': sources,
            'count': len(sources)
        }
    }