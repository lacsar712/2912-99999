"""
安全管理控制器
"""
from flask import Blueprint, request
from services.safety_service import SafetyService
from middleware.auth_middleware import login_required

safety_bp = Blueprint('safety', __name__)


@safety_bp.route('/hazard-types', methods=['GET'])
@login_required
def get_hazard_types():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    category = request.args.get('category')
    return SafetyService.get_hazard_types(page, size, category)


@safety_bp.route('/hazard-types', methods=['POST'])
@login_required
def create_hazard_type():
    data = request.get_json()
    return SafetyService.create_hazard_type(data)


@safety_bp.route('/hazard-types/<int:type_id>', methods=['PUT'])
@login_required
def update_hazard_type(type_id):
    data = request.get_json()
    return SafetyService.update_hazard_type(type_id, data)


@safety_bp.route('/hazard-types/<int:type_id>', methods=['DELETE'])
@login_required
def delete_hazard_type(type_id):
    return SafetyService.delete_hazard_type(type_id)


@safety_bp.route('/inspection-tasks', methods=['GET'])
@login_required
def get_inspection_tasks():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    task_type = request.args.get('taskType')
    return SafetyService.get_inspection_tasks(page, size, task_type)


@safety_bp.route('/inspection-tasks', methods=['POST'])
@login_required
def create_inspection_task():
    data = request.get_json()
    return SafetyService.create_inspection_task(data)


@safety_bp.route('/inspection-tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_inspection_task(task_id):
    data = request.get_json()
    return SafetyService.update_inspection_task(task_id, data)


@safety_bp.route('/inspection-tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_inspection_task(task_id):
    return SafetyService.delete_inspection_task(task_id)


@safety_bp.route('/hazard-records', methods=['GET'])
@login_required
def get_hazard_records():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    hazard_status = request.args.get('status')
    severity = request.args.get('severity')
    hazard_type_id = request.args.get('hazardTypeId', type=int)
    return SafetyService.get_hazard_records(page, size, hazard_status, severity, hazard_type_id)


@safety_bp.route('/hazard-records/<int:record_id>', methods=['GET'])
@login_required
def get_hazard_record(record_id):
    return SafetyService.get_hazard_record_by_id(record_id)


@safety_bp.route('/hazard-records', methods=['POST'])
@login_required
def create_hazard_record():
    data = request.get_json()
    return SafetyService.create_hazard_record(data)


@safety_bp.route('/hazard-records/<int:record_id>', methods=['PUT'])
@login_required
def update_hazard_record(record_id):
    data = request.get_json()
    return SafetyService.update_hazard_record(record_id, data)


@safety_bp.route('/hazard-records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_hazard_record(record_id):
    return SafetyService.delete_hazard_record(record_id)


@safety_bp.route('/hazard-records/<int:record_id>/accept', methods=['POST'])
@login_required
def accept_hazard(record_id):
    return SafetyService.accept_hazard(record_id)


@safety_bp.route('/rectification-records', methods=['GET'])
@login_required
def get_rectification_records():
    hazard_id = request.args.get('hazardId', type=int)
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    return SafetyService.get_rectification_records(hazard_id, page, size)


@safety_bp.route('/rectification-records', methods=['POST'])
@login_required
def create_rectification_record():
    data = request.get_json()
    return SafetyService.create_rectification_record(data)


@safety_bp.route('/rectification-records/<int:rect_id>', methods=['PUT'])
@login_required
def update_rectification_record(rect_id):
    data = request.get_json()
    return SafetyService.update_rectification_record(rect_id, data)


@safety_bp.route('/accident-records', methods=['GET'])
@login_required
def get_accident_records():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    severity = request.args.get('severity')
    return SafetyService.get_accident_records(page, size, severity)


@safety_bp.route('/accident-records/<int:record_id>', methods=['GET'])
@login_required
def get_accident_record(record_id):
    return SafetyService.get_accident_record_by_id(record_id)


@safety_bp.route('/accident-records', methods=['POST'])
@login_required
def create_accident_record():
    data = request.get_json()
    return SafetyService.create_accident_record(data)


@safety_bp.route('/accident-records/<int:record_id>', methods=['PUT'])
@login_required
def update_accident_record(record_id):
    data = request.get_json()
    return SafetyService.update_accident_record(record_id, data)


@safety_bp.route('/accident-records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_accident_record(record_id):
    return SafetyService.delete_accident_record(record_id)


@safety_bp.route('/check-overdue', methods=['POST'])
@login_required
def check_overdue():
    return SafetyService.check_overdue_hazards()


@safety_bp.route('/monthly-report', methods=['GET'])
@login_required
def get_monthly_report():
    months = request.args.get('months', 6, type=int)
    return SafetyService.get_monthly_report(months)
