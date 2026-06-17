"""
SOP标准作业管理控制器
"""
from flask import Blueprint, request
from services.sop_service import SOPService
from middleware.auth_middleware import login_required

sop_bp = Blueprint('sop', __name__)


# ==================== SOP文档 CRUD ====================

@sop_bp.route('/documents', methods=['GET'])
@login_required
def get_sops():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    status = request.args.get('status')
    keyword = request.args.get('keyword')
    equipment_id = request.args.get('equipment_id', type=int)
    product = request.args.get('product')
    return SOPService.get_sops(page, size, status, keyword, equipment_id, product)


@sop_bp.route('/documents/<int:sop_id>', methods=['GET'])
@login_required
def get_sop(sop_id):
    return SOPService.get_sop(sop_id)


@sop_bp.route('/documents', methods=['POST'])
@login_required
def create_sop():
    data = request.get_json()
    return SOPService.create_sop(data)


@sop_bp.route('/documents/<int:sop_id>', methods=['PUT'])
@login_required
def update_sop(sop_id):
    data = request.get_json()
    return SOPService.update_sop(sop_id, data)


@sop_bp.route('/documents/<int:sop_id>', methods=['DELETE'])
@login_required
def delete_sop(sop_id):
    return SOPService.delete_sop(sop_id)


# ==================== SOP发布与版本 ====================

@sop_bp.route('/documents/<int:sop_id>/publish', methods=['POST'])
@login_required
def publish_sop(sop_id):
    data = request.get_json() or {}
    return SOPService.publish_sop(sop_id, data)


@sop_bp.route('/documents/<int:sop_id>/diff', methods=['GET'])
@login_required
def get_version_diff(sop_id):
    v1 = request.args.get('version1_id', type=int)
    v2 = request.args.get('version2_id', type=int)
    return SOPService.get_version_diff(sop_id, v1, v2)


# ==================== 培训关联 ====================

@sop_bp.route('/documents/<int:sop_id>/training-relations', methods=['POST'])
@login_required
def add_training_relation(sop_id):
    data = request.get_json() or {}
    course_id = data.get('course_id')
    if not course_id:
        from utils.response import Response
        return Response.bad_request('缺少 course_id')
    return SOPService.add_training_relation(sop_id, course_id)


@sop_bp.route('/training-relations/<int:relation_id>', methods=['DELETE'])
@login_required
def remove_training_relation(relation_id):
    return SOPService.remove_training_relation(relation_id)


# ==================== 按设备/产品查询 ====================

@sop_bp.route('/by-equipment/<int:equipment_id>', methods=['GET'])
@login_required
def get_sops_by_equipment(equipment_id):
    return SOPService.get_sops_by_equipment(equipment_id)


@sop_bp.route('/by-product', methods=['GET'])
@login_required
def get_sops_by_product():
    product = request.args.get('name', '')
    return SOPService.get_sops_by_product(product)


# ==================== 执行检查表 ====================

@sop_bp.route('/checklists', methods=['GET'])
@login_required
def get_checklists():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    sop_id = request.args.get('sop_id', type=int)
    equipment_id = request.args.get('equipment_id', type=int)
    operator_id = request.args.get('operator_id', type=int)
    return SOPService.get_checklists(page, size, sop_id, equipment_id, operator_id)


@sop_bp.route('/checklists/<int:checklist_id>', methods=['GET'])
@login_required
def get_checklist(checklist_id):
    return SOPService.get_checklist(checklist_id)


@sop_bp.route('/checklists', methods=['POST'])
@login_required
def create_checklist():
    data = request.get_json()
    return SOPService.create_checklist(data)


@sop_bp.route('/checklists/<int:checklist_id>/items/<int:item_id>', methods=['PUT'])
@login_required
def update_checklist_item(checklist_id, item_id):
    data = request.get_json()
    return SOPService.update_checklist_item(checklist_id, item_id, data)


@sop_bp.route('/checklists/<int:checklist_id>/submit', methods=['POST'])
@login_required
def submit_checklist(checklist_id):
    data = request.get_json() or {}
    return SOPService.submit_checklist(checklist_id, data)


@sop_bp.route('/checklists/<int:checklist_id>', methods=['DELETE'])
@login_required
def delete_checklist(checklist_id):
    return SOPService.delete_checklist(checklist_id)


# ==================== 合规率统计 ====================

@sop_bp.route('/stats/compliance', methods=['GET'])
@login_required
def get_compliance_stats():
    sop_id = request.args.get('sop_id', type=int)
    equipment_id = request.args.get('equipment_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    return SOPService.get_compliance_stats(sop_id, equipment_id, start_date, end_date)
