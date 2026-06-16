"""
培训资质管理控制器
"""
from flask import Blueprint, request
from services.training_service import TrainingService
from middleware.auth_middleware import login_required

training_bp = Blueprint('training', __name__)


# ==================== 培训课程 ====================

@training_bp.route('/courses', methods=['GET'])
@login_required
def get_courses():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    category = request.args.get('category')
    return TrainingService.get_courses(page, size, category)


@training_bp.route('/courses/<int:course_id>', methods=['GET'])
@login_required
def get_course(course_id):
    return TrainingService.get_course(course_id)


@training_bp.route('/courses', methods=['POST'])
@login_required
def create_course():
    data = request.get_json()
    return TrainingService.create_course(data)


@training_bp.route('/courses/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    data = request.get_json()
    return TrainingService.update_course(course_id, data)


@training_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    return TrainingService.delete_course(course_id)


# ==================== 培训计划 ====================

@training_bp.route('/plans', methods=['GET'])
@login_required
def get_plans():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    status = request.args.get('status')
    course_id = request.args.get('course_id', type=int)
    return TrainingService.get_plans(page, size, status, course_id)


@training_bp.route('/plans/<int:plan_id>', methods=['GET'])
@login_required
def get_plan(plan_id):
    return TrainingService.get_plan(plan_id)


@training_bp.route('/plans', methods=['POST'])
@login_required
def create_plan():
    data = request.get_json()
    return TrainingService.create_plan(data)


@training_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@login_required
def update_plan(plan_id):
    data = request.get_json()
    return TrainingService.update_plan(plan_id, data)


@training_bp.route('/plans/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    return TrainingService.delete_plan(plan_id)


# ==================== 参训记录 ====================

@training_bp.route('/attendances', methods=['GET'])
@login_required
def get_attendances():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    plan_id = request.args.get('plan_id', type=int)
    user_id = request.args.get('user_id', type=int)
    sign_in_status = request.args.get('sign_in_status')
    return TrainingService.get_attendances(page, size, plan_id, user_id, sign_in_status)


@training_bp.route('/attendances/<int:attendance_id>', methods=['GET'])
@login_required
def get_attendance(attendance_id):
    return TrainingService.get_attendance(attendance_id)


@training_bp.route('/attendances', methods=['POST'])
@login_required
def create_attendance():
    data = request.get_json()
    return TrainingService.create_attendance(data)


@training_bp.route('/attendances/batch', methods=['POST'])
@login_required
def batch_create_attendances():
    plan_id = request.args.get('plan_id', type=int)
    data = request.get_json()
    return TrainingService.batch_create_attendances(plan_id, data)


@training_bp.route('/attendances/<int:attendance_id>', methods=['PUT'])
@login_required
def update_attendance(attendance_id):
    data = request.get_json()
    return TrainingService.update_attendance(attendance_id, data)


@training_bp.route('/attendances/<int:attendance_id>/sign-in', methods=['POST'])
@login_required
def sign_in(attendance_id):
    return TrainingService.sign_in(attendance_id)


@training_bp.route('/attendances/<int:attendance_id>', methods=['DELETE'])
@login_required
def delete_attendance(attendance_id):
    return TrainingService.delete_attendance(attendance_id)


# ==================== 资质证书 ====================

@training_bp.route('/certificates', methods=['GET'])
@login_required
def get_certificates():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    certificate_type = request.args.get('certificate_type')
    expiry_status = request.args.get('expiry_status')
    return TrainingService.get_certificates(page, size, user_id, certificate_type, expiry_status)


@training_bp.route('/certificates/<int:cert_id>', methods=['GET'])
@login_required
def get_certificate(cert_id):
    return TrainingService.get_certificate(cert_id)


@training_bp.route('/certificates', methods=['POST'])
@login_required
def create_certificate():
    data = request.get_json()
    return TrainingService.create_certificate(data)


@training_bp.route('/certificates/<int:cert_id>', methods=['PUT'])
@login_required
def update_certificate(cert_id):
    data = request.get_json()
    return TrainingService.update_certificate(cert_id, data)


@training_bp.route('/certificates/<int:cert_id>', methods=['DELETE'])
@login_required
def delete_certificate(cert_id):
    return TrainingService.delete_certificate(cert_id)


# ==================== 岗位资质要求 ====================

@training_bp.route('/position-qualifications', methods=['GET'])
@login_required
def get_position_qualifications():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    return TrainingService.get_position_qualifications(page, size)


@training_bp.route('/position-qualifications/<int:pq_id>', methods=['GET'])
@login_required
def get_position_qualification(pq_id):
    return TrainingService.get_position_qualification(pq_id)


@training_bp.route('/position-qualifications', methods=['POST'])
@login_required
def create_position_qualification():
    data = request.get_json()
    return TrainingService.create_position_qualification(data)


@training_bp.route('/position-qualifications/<int:pq_id>', methods=['PUT'])
@login_required
def update_position_qualification(pq_id):
    data = request.get_json()
    return TrainingService.update_position_qualification(pq_id, data)


@training_bp.route('/position-qualifications/<int:pq_id>', methods=['DELETE'])
@login_required
def delete_position_qualification(pq_id):
    return TrainingService.delete_position_qualification(pq_id)


# ==================== 资质校验接口 ====================

@training_bp.route('/qualifications/check/<int:user_id>', methods=['GET'])
@login_required
def check_user_qualification(user_id):
    return TrainingService.check_user_qualification(user_id)


@training_bp.route('/qualifications/check-all', methods=['POST'])
@login_required
def check_all_qualifications():
    return TrainingService.check_all_qualifications()


@training_bp.route('/qualifications/matrix', methods=['GET'])
@login_required
def get_qualification_matrix():
    return TrainingService.get_qualification_matrix()


# ==================== 证书到期检测 ====================

@training_bp.route('/certificates/check-expiring', methods=['POST'])
@login_required
def check_expiring_certificates():
    days = request.args.get('days', 30, type=int)
    return TrainingService.check_expiring_certificates(days)
