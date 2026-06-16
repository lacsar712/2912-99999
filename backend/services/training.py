"""
培训与资质管理服务模块
"""
from datetime import datetime, timedelta
from database.db import db
from models.training import TrainingCourse, TrainingPlan, TrainingAttendance, QualificationCertificate, PositionQualification
from models.production import AlertRecord
from models.user import User
from utils.response import Response
from utils.validator import Validator


class TrainingService:
    """培训与资质服务类"""

    # ==================== 培训课程 CRUD ====================

    @staticmethod
    def get_courses(page=1, size=20, category=None):
        query = TrainingCourse.query
        if category:
            query = query.filter(TrainingCourse.category == category)
        query = query.filter(TrainingCourse.status == 1)
        pagination = query.order_by(TrainingCourse.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_course(course_id):
        course = TrainingCourse.get_by_id(course_id)
        if not course:
            return Response.not_found('培训课程不存在')
        return Response.success(course.to_dict())

    @staticmethod
    def create_course(data):
        validation = Validator.validate_form(data, {
            'course_code': ['required'],
            'course_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        if TrainingCourse.query.filter_by(course_code=data['course_code']).first():
            return Response.bad_request('课程编号已存在')
        course = TrainingCourse(
            course_code=data['course_code'],
            course_name=data['course_name'],
            category=data.get('category'),
            lecturer=data.get('lecturer'),
            planned_duration=data.get('planned_duration', 0),
            assessment_form=data.get('assessment_form'),
            attachment_base64=data.get('attachment_base64'),
            description=data.get('description')
        )
        db.session.add(course)
        db.session.commit()
        return Response.created(course.to_dict())

    @staticmethod
    def update_course(course_id, data):
        course = TrainingCourse.get_by_id(course_id)
        if not course:
            return Response.not_found('培训课程不存在')
        if 'course_code' in data and data['course_code'] != course.course_code:
            if TrainingCourse.query.filter_by(course_code=data['course_code']).first():
                return Response.bad_request('课程编号已存在')
            course.course_code = data['course_code']
        for key in ['course_name', 'category', 'lecturer', 'planned_duration',
                    'assessment_form', 'attachment_base64', 'description']:
            if key in data:
                setattr(course, key, data[key])
        db.session.commit()
        return Response.success(course.to_dict())

    @staticmethod
    def delete_course(course_id):
        course = TrainingCourse.get_by_id(course_id)
        if not course:
            return Response.not_found('培训课程不存在')
        course.delete()
        return Response.success(message='删除成功')

    # ==================== 培训计划 CRUD ====================

    @staticmethod
    def get_plans(page=1, size=20, status=None, course_id=None):
        query = TrainingPlan.query
        if status:
            query = query.filter(TrainingPlan.status == status)
        else:
            query = query.filter(TrainingPlan.status != 'cancelled')
        if course_id:
            query = query.filter(TrainingPlan.course_id == course_id)
        pagination = query.order_by(TrainingPlan.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_plan(plan_id):
        plan = TrainingPlan.get_by_id(plan_id)
        if not plan:
            return Response.not_found('培训计划不存在')
        result = plan.to_dict()
        result['attendances'] = [a.to_dict() for a in plan.attendances.all()]
        result['trainee_ids'] = plan.get_trainee_ids()
        return Response.success(result)

    @staticmethod
    def create_plan(data):
        validation = Validator.validate_form(data, {
            'plan_name': ['required'],
            'course_id': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        course = TrainingCourse.get_by_id(data['course_id'])
        if not course:
            return Response.bad_request('关联的培训课程不存在')
        now = datetime.now()
        plan_code = f"TP-{now.strftime('%Y%m%d%H%M%S')}-{TrainingPlan.query.count() + 1}"
        start_time = None
        if data.get('start_time'):
            start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = None
        if data.get('end_time'):
            end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        plan = TrainingPlan(
            plan_code=plan_code,
            plan_name=data['plan_name'],
            course_id=data['course_id'],
            start_time=start_time,
            end_time=end_time,
            location=data.get('location'),
            status=data.get('status', 'draft'),
            description=data.get('description')
        )
        if data.get('trainee_ids'):
            plan.set_trainee_ids(data['trainee_ids'])
        db.session.add(plan)
        db.session.commit()
        return Response.created(plan.to_dict())

    @staticmethod
    def update_plan(plan_id, data):
        plan = TrainingPlan.get_by_id(plan_id)
        if not plan:
            return Response.not_found('培训计划不存在')
        if 'course_id' in data:
            course = TrainingCourse.get_by_id(data['course_id'])
            if not course:
                return Response.bad_request('关联的培训课程不存在')
            plan.course_id = data['course_id']
        for key in ['plan_name', 'location', 'status', 'description']:
            if key in data:
                setattr(plan, key, data[key])
        if 'start_time' in data and data['start_time']:
            plan.start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        if 'end_time' in data and data['end_time']:
            plan.end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        if 'trainee_ids' in data:
            plan.set_trainee_ids(data['trainee_ids'])
        db.session.commit()
        return Response.success(plan.to_dict())

    @staticmethod
    def delete_plan(plan_id):
        plan = TrainingPlan.get_by_id(plan_id)
        if not plan:
            return Response.not_found('培训计划不存在')
        plan.status = 'cancelled'
        db.session.commit()
        return Response.success(message='删除成功')

    # ==================== 参训记录 CRUD ====================

    @staticmethod
    def get_attendances(page=1, size=20, plan_id=None, user_id=None, sign_in_status=None):
        query = TrainingAttendance.query
        if plan_id:
            query = query.filter(TrainingAttendance.plan_id == plan_id)
        if user_id:
            query = query.filter(TrainingAttendance.user_id == user_id)
        if sign_in_status:
            query = query.filter(TrainingAttendance.sign_in_status == sign_in_status)
        query = query.filter(TrainingAttendance.status == 1)
        pagination = query.order_by(TrainingAttendance.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_attendance(attendance_id):
        attendance = TrainingAttendance.get_by_id(attendance_id)
        if not attendance:
            return Response.not_found('参训记录不存在')
        return Response.success(attendance.to_dict())

    @staticmethod
    def create_attendance(data):
        validation = Validator.validate_form(data, {
            'plan_id': ['required'],
            'user_id': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        plan = TrainingPlan.get_by_id(data['plan_id'])
        if not plan:
            return Response.bad_request('培训计划不存在')
        user = User.get_by_id(data['user_id'])
        if not user:
            return Response.bad_request('员工不存在')
        existing = TrainingAttendance.query.filter_by(
            plan_id=data['plan_id'],
            user_id=data['user_id']
        ).first()
        if existing:
            return Response.bad_request('该员工已存在此计划的参训记录')
        final_score = data.get('final_score')
        if final_score is not None:
            final_score = float(final_score)
        attendance = TrainingAttendance(
            plan_id=data['plan_id'],
            user_id=data['user_id'],
            sign_in_status=data.get('sign_in_status', 'not_signed'),
            sign_in_time=datetime.strptime(data['sign_in_time'], '%Y-%m-%d %H:%M:%S') if data.get('sign_in_time') else None,
            final_score=final_score,
            is_passed=data.get('is_passed', False),
            remark=data.get('remark')
        )
        db.session.add(attendance)
        db.session.commit()
        return Response.created(attendance.to_dict())

    @staticmethod
    def batch_create_attendances(plan_id):
        plan = TrainingPlan.get_by_id(plan_id)
        if not plan:
            return Response.not_found('培训计划不存在')
        trainee_ids = plan.get_trainee_ids()
        if not trainee_ids:
            return Response.bad_request('该计划未设置受训人员')
        created_count = 0
        skipped_count = 0
        for user_id in trainee_ids:
            user = User.get_by_id(user_id)
            if not user:
                skipped_count += 1
                continue
            existing = TrainingAttendance.query.filter_by(
                plan_id=plan_id,
                user_id=user_id
            ).first()
            if existing:
                skipped_count += 1
                continue
            attendance = TrainingAttendance(
                plan_id=plan_id,
                user_id=user_id,
                sign_in_status='not_signed',
                is_passed=False
            )
            db.session.add(attendance)
            created_count += 1
        db.session.commit()
        return Response.success({
            'created_count': created_count,
            'skipped_count': skipped_count,
            'total_trainees': len(trainee_ids)
        })

    @staticmethod
    def update_attendance(attendance_id, data):
        attendance = TrainingAttendance.get_by_id(attendance_id)
        if not attendance:
            return Response.not_found('参训记录不存在')
        for key in ['sign_in_status', 'is_passed', 'remark']:
            if key in data:
                setattr(attendance, key, data[key])
        if 'sign_in_time' in data and data['sign_in_time']:
            attendance.sign_in_time = datetime.strptime(data['sign_in_time'], '%Y-%m-%d %H:%M:%S')
        if 'final_score' in data and data['final_score'] is not None:
            attendance.final_score = float(data['final_score'])
        db.session.commit()
        return Response.success(attendance.to_dict())

    @staticmethod
    def sign_in(attendance_id, data):
        attendance = TrainingAttendance.get_by_id(attendance_id)
        if not attendance:
            return Response.not_found('参训记录不存在')
        sign_in_status = data.get('sign_in_status', 'signed_in')
        if sign_in_status not in ['signed_in', 'late', 'absent', 'leave']:
            return Response.bad_request('无效的签到状态')
        attendance.sign_in_status = sign_in_status
        attendance.sign_in_time = datetime.now()
        if 'remark' in data:
            attendance.remark = data['remark']
        db.session.commit()
        return Response.success(attendance.to_dict())

    @staticmethod
    def delete_attendance(attendance_id):
        attendance = TrainingAttendance.get_by_id(attendance_id)
        if not attendance:
            return Response.not_found('参训记录不存在')
        attendance.delete()
        return Response.success(message='删除成功')

    # ==================== 资质证书 CRUD ====================

    @staticmethod
    def get_certificates(page=1, size=20, user_id=None, certificate_type=None, expiry_status=None):
        query = QualificationCertificate.query
        if user_id:
            query = query.filter(QualificationCertificate.user_id == user_id)
        if certificate_type:
            query = query.filter(QualificationCertificate.certificate_type == certificate_type)
        query = query.filter(QualificationCertificate.status == 1)
        if expiry_status:
            today = datetime.now().date()
            if expiry_status == 'expired':
                query = query.filter(
                    QualificationCertificate.expiry_date != None,
                    QualificationCertificate.expiry_date < today
                )
            elif expiry_status == 'expiring_soon':
                threshold_date = today + timedelta(days=30)
                query = query.filter(
                    QualificationCertificate.expiry_date != None,
                    QualificationCertificate.expiry_date >= today,
                    QualificationCertificate.expiry_date <= threshold_date
                )
            elif expiry_status == 'valid':
                query = query.filter(
                    db.or_(
                        QualificationCertificate.expiry_date == None,
                        QualificationCertificate.expiry_date >= today
                    )
                )
            elif expiry_status == 'permanent':
                query = query.filter(QualificationCertificate.expiry_date == None)
        query = query.order_by(QualificationCertificate.create_time.desc())
        pagination = query.paginate(page=page, per_page=size, error_out=False)
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_certificate(cert_id):
        cert = QualificationCertificate.get_by_id(cert_id)
        if not cert:
            return Response.not_found('资质证书不存在')
        return Response.success(cert.to_dict())

    @staticmethod
    def create_certificate(data):
        validation = Validator.validate_form(data, {
            'user_id': ['required'],
            'certificate_type': ['required'],
            'certificate_number': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        user = User.get_by_id(data['user_id'])
        if not user:
            return Response.bad_request('员工不存在')
        if QualificationCertificate.query.filter_by(certificate_number=data['certificate_number']).first():
            return Response.bad_request('证书编号已存在')
        issue_date = None
        if data.get('issue_date'):
            issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
        expiry_date = None
        if data.get('expiry_date'):
            expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
        cert = QualificationCertificate(
            user_id=data['user_id'],
            certificate_type=data['certificate_type'],
            certificate_number=data['certificate_number'],
            issue_date=issue_date,
            expiry_date=expiry_date,
            attachment_base64=data.get('attachment_base64'),
            issuer=data.get('issuer'),
            remark=data.get('remark')
        )
        db.session.add(cert)
        db.session.commit()
        return Response.created(cert.to_dict())

    @staticmethod
    def update_certificate(cert_id, data):
        cert = QualificationCertificate.get_by_id(cert_id)
        if not cert:
            return Response.not_found('资质证书不存在')
        if 'certificate_number' in data and data['certificate_number'] != cert.certificate_number:
            if QualificationCertificate.query.filter_by(certificate_number=data['certificate_number']).first():
                return Response.bad_request('证书编号已存在')
            cert.certificate_number = data['certificate_number']
        if 'user_id' in data:
            user = User.get_by_id(data['user_id'])
            if not user:
                return Response.bad_request('员工不存在')
            cert.user_id = data['user_id']
        for key in ['certificate_type', 'attachment_base64', 'issuer', 'remark']:
            if key in data:
                setattr(cert, key, data[key])
        if 'issue_date' in data and data['issue_date']:
            cert.issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
        if 'expiry_date' in data:
            if data['expiry_date']:
                cert.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            else:
                cert.expiry_date = None
        db.session.commit()
        return Response.success(cert.to_dict())

    @staticmethod
    def delete_certificate(cert_id):
        cert = QualificationCertificate.get_by_id(cert_id)
        if not cert:
            return Response.not_found('资质证书不存在')
        cert.delete()
        return Response.success(message='删除成功')

    # ==================== 岗位资质要求 CRUD ====================

    @staticmethod
    def get_position_qualifications(page=1, size=20):
        query = PositionQualification.query
        query = query.filter(PositionQualification.status == 1)
        pagination = query.order_by(PositionQualification.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_position_qualification(pq_id):
        pq = PositionQualification.get_by_id(pq_id)
        if not pq:
            return Response.not_found('岗位资质要求不存在')
        return Response.success(pq.to_dict())

    @staticmethod
    def create_position_qualification(data):
        validation = Validator.validate_form(data, {
            'position_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        if PositionQualification.query.filter_by(position_name=data['position_name']).first():
            return Response.bad_request('岗位名称已存在')
        pq = PositionQualification(
            position_name=data['position_name'],
            description=data.get('description')
        )
        if data.get('certificate_list'):
            pq.set_required_cert_list(data['certificate_list'])
        db.session.add(pq)
        db.session.commit()
        return Response.created(pq.to_dict())

    @staticmethod
    def update_position_qualification(pq_id, data):
        pq = PositionQualification.get_by_id(pq_id)
        if not pq:
            return Response.not_found('岗位资质要求不存在')
        if 'position_name' in data and data['position_name'] != pq.position_name:
            if PositionQualification.query.filter_by(position_name=data['position_name']).first():
                return Response.bad_request('岗位名称已存在')
            pq.position_name = data['position_name']
        if 'description' in data:
            pq.description = data['description']
        if 'certificate_list' in data:
            pq.set_required_cert_list(data['certificate_list'])
        db.session.commit()
        return Response.success(pq.to_dict())

    @staticmethod
    def delete_position_qualification(pq_id):
        pq = PositionQualification.get_by_id(pq_id)
        if not pq:
            return Response.not_found('岗位资质要求不存在')
        pq.delete()
        return Response.success(message='删除成功')

    # ==================== 资质合规校验 ====================

    @staticmethod
    def check_user_qualification(user_id):
        user = User.get_by_id(user_id)
        if not user:
            return Response.not_found('员工不存在')
        position_name = user.position or ''
        required_certs = []
        if position_name:
            pq = PositionQualification.query.filter_by(
                position_name=position_name,
                status=1
            ).first()
            if pq:
                required_certs = pq.get_required_cert_list()
        user_certs = QualificationCertificate.query.filter_by(
            user_id=user_id,
            status=1
        ).all()
        valid_certs = []
        valid_cert_types = set()
        for cert in user_certs:
            if cert.is_valid():
                valid_certs.append(cert.to_dict())
                valid_cert_types.add(cert.certificate_type)
        missing_certs = [cert_type for cert_type in required_certs if cert_type not in valid_cert_types]
        compliant = len(missing_certs) == 0
        return Response.success({
            'compliant': compliant,
            'missing_certs': missing_certs,
            'position': position_name,
            'certificates': valid_certs,
            'required_certificates': required_certs
        })

    @staticmethod
    def check_all_qualifications():
        users = User.get_all()
        non_compliant_users = []
        alert_count = 0
        for user in users:
            position_name = user.position or ''
            required_certs = []
            if position_name:
                pq = PositionQualification.query.filter_by(
                    position_name=position_name,
                    status=1
                ).first()
                if pq:
                    required_certs = pq.get_required_cert_list()
            if not required_certs:
                continue
            user_certs = QualificationCertificate.query.filter_by(
                user_id=user.id,
                status=1
            ).all()
            valid_cert_types = set()
            for cert in user_certs:
                if cert.is_valid():
                    valid_cert_types.add(cert.certificate_type)
            missing_certs = [cert_type for cert_type in required_certs if cert_type not in valid_cert_types]
            if missing_certs:
                non_compliant_users.append({
                    'user_id': user.id,
                    'username': user.username,
                    'position': position_name,
                    'missing_certs': missing_certs
                })
                existing_alert = AlertRecord.query.filter(
                    AlertRecord.alert_type == 'training_required',
                    AlertRecord.status == 'active',
                    AlertRecord.message.like(f'%{user.username}%')
                ).first()
                if not existing_alert:
                    now = datetime.now()
                    alert_code = f"ALERT-{now.strftime('%Y%m%d%H%M%S')}-TR-{user.id}"
                    missing_str = '、'.join(missing_certs)
                    alert = AlertRecord(
                        alert_code=alert_code,
                        alert_type='training_required',
                        severity='warning',
                        message=f'员工"{user.username}"岗位"{position_name}"缺少资质证书：{missing_str}，请及时安排培训！',
                        status='active'
                    )
                    db.session.add(alert)
                    alert_count += 1
        db.session.commit()
        return Response.success({
            'total_checked': len(users),
            'non_compliant_count': len(non_compliant_users),
            'alert_generated_count': alert_count,
            'non_compliant_users': non_compliant_users
        })

    @staticmethod
    def get_qualification_matrix():
        all_pqs = PositionQualification.query.filter_by(status=1).all()
        positions = []
        required_certs_map = {}
        for pq in all_pqs:
            positions.append(pq.position_name)
            required_certs_map[pq.position_name] = pq.get_required_cert_list()
        all_cert_types = set()
        for cert_list in required_certs_map.values():
            for cert_type in cert_list:
                all_cert_types.add(cert_type)
        all_cert_types = sorted(list(all_cert_types))
        users = User.get_all()
        user_list = []
        matrix = {}
        for user in users:
            position_name = user.position or ''
            user_certs = QualificationCertificate.query.filter_by(
                user_id=user.id,
                status=1
            ).all()
            certs_by_type = {}
            for cert_type in all_cert_types:
                certs_by_type[cert_type] = False
            for cert in user_certs:
                if cert.is_valid() and cert.certificate_type in certs_by_type:
                    certs_by_type[cert.certificate_type] = True
            required = required_certs_map.get(position_name, [])
            compliance_status = True
            for cert_type in required:
                if not certs_by_type.get(cert_type, False):
                    compliance_status = False
                    break
            user_entry = {
                'id': user.id,
                'username': user.username,
                'position': position_name,
                'compliance_status': compliance_status,
                'certs_by_type': certs_by_type
            }
            user_list.append(user_entry)
            matrix[user.id] = {}
            for pos in positions:
                pos_required = required_certs_map.get(pos, [])
                pos_compliant = True
                for cert_type in pos_required:
                    if not certs_by_type.get(cert_type, False):
                        pos_compliant = False
                        break
                matrix[user.id][pos] = pos_compliant
        return Response.success({
            'positions': positions,
            'certificate_types': all_cert_types,
            'users': user_list,
            'matrix': matrix
        })

    # ==================== 证书到期检测 ====================

    @staticmethod
    def check_expiring_certificates(days=30):
        now = datetime.now()
        today = now.date()
        expiring_certs = []
        alert_count = 0
        all_certs = QualificationCertificate.query.filter_by(status=1).all()
        for cert in all_certs:
            if not cert.expiry_date:
                continue
            days_left = (cert.expiry_date - today).days
            if days_left < 0:
                continue
            if days_left <= days:
                severity = 'warning'
                if days_left <= 7:
                    severity = 'critical'
                elif days_left <= 15:
                    severity = 'error'
                user = User.get_by_id(cert.user_id)
                username = user.username if user else '未知'
                expiring_certs.append({
                    'id': cert.id,
                    'certificate_number': cert.certificate_number,
                    'certificate_type': cert.certificate_type,
                    'username': username,
                    'user_id': cert.user_id,
                    'expiry_date': cert.expiry_date.strftime('%Y-%m-%d'),
                    'days_left': days_left,
                    'severity': severity
                })
                existing_alert = AlertRecord.query.filter(
                    AlertRecord.alert_type == 'certificate_expiring',
                    AlertRecord.status == 'active',
                    AlertRecord.message.like(f'%{cert.certificate_number}%')
                ).first()
                if not existing_alert:
                    alert_code = f"ALERT-{now.strftime('%Y%m%d%H%M%S')}-CE-{cert.id}"
                    if days_left == 0:
                        day_text = '今天'
                    else:
                        day_text = f'{days_left}天内'
                    alert = AlertRecord(
                        alert_code=alert_code,
                        alert_type='certificate_expiring',
                        severity=severity,
                        message=f'员工"{username}"的"{cert.certificate_type}"证书({cert.certificate_number})将在{day_text}到期，请及时续证！',
                        status='active'
                    )
                    db.session.add(alert)
                    alert_count += 1
        db.session.commit()
        expiring_certs.sort(key=lambda x: x['days_left'])
        return Response.success({
            'checked_count': len(all_certs),
            'expiring_count': len(expiring_certs),
            'alert_generated_count': alert_count,
            'expiring_certificates': expiring_certs
        })
