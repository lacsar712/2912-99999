"""
视频监控控制器
"""
from flask import Blueprint, request
from services.video_monitor_service import (
    CameraService, PatrolGroupService, CaptureRecordService
)
from middleware.auth_middleware import login_required

video_monitor_bp = Blueprint('video_monitor', __name__)


@video_monitor_bp.route('/cameras', methods=['GET'])
@login_required
def get_cameras():
    """获取摄像头列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword')
    online_status = request.args.get('online_status')
    line_id = request.args.get('line_id', type=int)

    return CameraService.get_cameras(page, size, keyword, online_status, line_id)


@video_monitor_bp.route('/cameras/all', methods=['GET'])
@login_required
def get_all_cameras():
    """获取所有摄像头（不分页）"""
    return CameraService.get_all_cameras()


@video_monitor_bp.route('/cameras/<int:camera_id>', methods=['GET'])
@login_required
def get_camera(camera_id):
    """获取摄像头详情"""
    return CameraService.get_camera_by_id(camera_id)


@video_monitor_bp.route('/cameras', methods=['POST'])
@login_required
def create_camera():
    """创建摄像头"""
    data = request.get_json()
    return CameraService.create_camera(data)


@video_monitor_bp.route('/cameras/<int:camera_id>', methods=['PUT'])
@login_required
def update_camera(camera_id):
    """更新摄像头"""
    data = request.get_json()
    return CameraService.update_camera(camera_id, data)


@video_monitor_bp.route('/cameras/<int:camera_id>', methods=['DELETE'])
@login_required
def delete_camera(camera_id):
    """删除摄像头"""
    return CameraService.delete_camera(camera_id)


@video_monitor_bp.route('/cameras/heartbeat', methods=['POST'])
def report_heartbeat():
    """摄像头心跳上报（无需登录）"""
    data = request.get_json() or {}
    camera_code = data.get('camera_code') or request.args.get('camera_code')
    camera_id = data.get('camera_id') or request.args.get('camera_id', type=int)

    return CameraService.report_heartbeat(camera_code=camera_code, camera_id=camera_id)


@video_monitor_bp.route('/groups', methods=['GET'])
@login_required
def get_groups():
    """获取巡视分组列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword')

    return PatrolGroupService.get_groups(page, size, keyword)


@video_monitor_bp.route('/groups/all', methods=['GET'])
@login_required
def get_all_groups():
    """获取所有分组"""
    return PatrolGroupService.get_all_groups()


@video_monitor_bp.route('/groups/<int:group_id>', methods=['GET'])
@login_required
def get_group(group_id):
    """获取分组详情"""
    return PatrolGroupService.get_group_by_id(group_id)


@video_monitor_bp.route('/groups/<int:group_id>/online-cameras', methods=['GET'])
@login_required
def get_group_online_cameras(group_id):
    """按分组获取当前在线摄像头"""
    return PatrolGroupService.get_group_online_cameras(group_id)


@video_monitor_bp.route('/groups', methods=['POST'])
@login_required
def create_group():
    """创建分组"""
    data = request.get_json()
    return PatrolGroupService.create_group(data)


@video_monitor_bp.route('/groups/<int:group_id>', methods=['PUT'])
@login_required
def update_group(group_id):
    """更新分组"""
    data = request.get_json()
    return PatrolGroupService.update_group(group_id, data)


@video_monitor_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@login_required
def delete_group(group_id):
    """删除分组"""
    return PatrolGroupService.delete_group(group_id)


@video_monitor_bp.route('/captures', methods=['GET'])
@login_required
def get_capture_records():
    """获取抓图记录列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    source = request.args.get('source')
    camera_id = request.args.get('camera_id', type=int)
    alert_id = request.args.get('alert_id', type=int)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    return CaptureRecordService.get_records(
        page, size, source, camera_id, alert_id, start_time, end_time
    )


@video_monitor_bp.route('/captures/alert/<int:alert_id>', methods=['GET'])
@login_required
def get_captures_by_alert(alert_id):
    """根据告警ID获取抓图记录"""
    return CaptureRecordService.get_records_by_alert(alert_id)


@video_monitor_bp.route('/captures/<int:record_id>', methods=['GET'])
@login_required
def get_capture_record(record_id):
    """获取抓图记录详情"""
    return CaptureRecordService.get_record_by_id(record_id)


@video_monitor_bp.route('/captures/manual/<int:camera_id>', methods=['POST'])
@login_required
def create_manual_capture(camera_id):
    """手动抓图"""
    return CaptureRecordService.create_manual_capture(camera_id)


@video_monitor_bp.route('/captures/alert-trigger', methods=['POST'])
@login_required
def trigger_alert_capture():
    """告警触发自动抓图接口"""
    data = request.get_json()
    alert_id = data.get('alert_id')
    equipment_id = data.get('equipment_id')

    if not alert_id:
        from utils.response import Response
        return Response.bad_request('缺少告警ID')

    return CaptureRecordService.create_alert_capture(alert_id, equipment_id)
