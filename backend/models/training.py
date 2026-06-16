"""
培训与资质管理模型
"""
from datetime import datetime, timedelta
from database.db import db
from models.base import BaseModel


class TrainingCourse(BaseModel):
    """培训课程"""
    __tablename__ = 'training_course'

    course_code = db.Column(db.String(50), unique=True, nullable=False, comment='课程编号')
    course_name = db.Column(db.String(200), nullable=False, comment='课程名称')
    category = db.Column(db.String(50), comment='课程类别(安全/技能/管理/其他)')
    lecturer = db.Column(db.String(100), comment='讲师')
    planned_duration = db.Column(db.Integer, default=0, comment='计划时长(小时)')
    assessment_form = db.Column(db.String(50), comment='考核形式(考试/实操/论文/考勤)')
    attachment_base64 = db.Column(db.Text, comment='课程附件(base64)')
    description = db.Column(db.Text, comment='课程描述')

    plans = db.relationship('TrainingPlan', backref='course', lazy='dynamic')

    def __repr__(self):
        return f'<TrainingCourse {self.course_name}>'


class TrainingPlan(BaseModel):
    """培训计划"""
    __tablename__ = 'training_plan'

    plan_code = db.Column(db.String(50), unique=True, nullable=False, comment='计划编号')
    plan_name = db.Column(db.String(200), nullable=False, comment='计划名称')
    course_id = db.Column(db.BigInteger, db.ForeignKey('training_course.id'), nullable=False, comment='课程ID')
    target_trainees = db.Column(db.Text, comment='目标受训人员(逗号分隔的用户ID列表)')
    start_time = db.Column(db.DateTime, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    location = db.Column(db.String(200), comment='培训地点')
    status = db.Column(
        db.Enum('draft', 'published', 'ongoing', 'completed', 'cancelled'),
        default='draft',
        comment='状态: 草稿/已发布/进行中/已完成/已取消'
    )
    description = db.Column(db.Text, comment='计划描述')

    attendances = db.relationship('TrainingAttendance', backref='plan', lazy='dynamic',
                                  cascade='all, delete-orphan')

    def to_dict(self):
        result = super().to_dict()
        if self.course:
            result['course_name'] = self.course.course_name
            result['course_code'] = self.course.course_code
            result['category'] = self.course.category
            result['lecturer'] = self.course.lecturer
            result['planned_duration'] = self.course.planned_duration
        result['trainee_count'] = len(self.get_trainee_ids()) if self.target_trainees else 0
        return result

    def get_trainee_ids(self):
        """获取受训人员ID列表"""
        if not self.target_trainees:
            return []
        return [int(x.strip()) for x in self.target_trainees.split(',') if x.strip()]

    def set_trainee_ids(self, ids):
        """设置受训人员ID列表"""
        if ids:
            self.target_trainees = ','.join(str(x) for x in ids)
        else:
            self.target_trainees = None

    def __repr__(self):
        return f'<TrainingPlan {self.plan_name}>'


class TrainingAttendance(BaseModel):
    """参训记录"""
    __tablename__ = 'training_attendance'

    plan_id = db.Column(db.BigInteger, db.ForeignKey('training_plan.id'), nullable=False, comment='培训计划ID')
    user_id = db.Column(db.BigInteger, db.ForeignKey('t_user.id'), nullable=False, comment='员工ID')
    sign_in_status = db.Column(
        db.Enum('not_signed', 'signed_in', 'late', 'absent', 'leave'),
        default='not_signed',
        comment='签到状态: 未签到/已签到/迟到/缺勤/请假'
    )
    sign_in_time = db.Column(db.DateTime, comment='签到时间')
    final_score = db.Column(db.Numeric(5, 2), comment='最终成绩')
    is_passed = db.Column(db.Boolean, default=False, comment='是否合格')
    remark = db.Column(db.Text, comment='备注')

    __table_args__ = (
        db.UniqueConstraint('plan_id', 'user_id', name='uk_plan_user'),
    )

    def to_dict(self):
        result = super().to_dict()
        if self.plan:
            result['plan_name'] = self.plan.plan_name
            result['plan_code'] = self.plan.plan_code
        try:
            from models.user import User
            user = User.get_by_id(self.user_id)
            if user:
                result['username'] = user.username
                result['email'] = user.email
                result['position'] = getattr(user, 'position', None)
        except Exception:
            pass
        return result

    def __repr__(self):
        return f'<TrainingAttendance plan={self.plan_id} user={self.user_id}>'


class QualificationCertificate(BaseModel):
    """资质证书"""
    __tablename__ = 'qualification_certificate'

    user_id = db.Column(db.BigInteger, db.ForeignKey('t_user.id'), nullable=False, comment='员工ID')
    certificate_type = db.Column(db.String(100), nullable=False, comment='证书类型')
    certificate_number = db.Column(db.String(100), unique=True, nullable=False, comment='证书编号')
    issue_date = db.Column(db.Date, comment='获取时间')
    expiry_date = db.Column(db.Date, comment='有效期(到期日期)')
    attachment_base64 = db.Column(db.Text, comment='证书附件(base64)')
    issuer = db.Column(db.String(200), comment='发证机构')
    remark = db.Column(db.Text, comment='备注')

    def to_dict(self):
        result = super().to_dict()
        try:
            from models.user import User
            user = User.get_by_id(self.user_id)
            if user:
                result['username'] = user.username
                result['email'] = user.email
                result['position'] = getattr(user, 'position', None)
        except Exception:
            pass
        if self.expiry_date:
            today = datetime.now().date()
            days_left = (self.expiry_date - today).days
            result['days_to_expiry'] = days_left
            if days_left < 0:
                result['expiry_status'] = 'expired'
            elif days_left <= 30:
                result['expiry_status'] = 'expiring_soon'
            else:
                result['expiry_status'] = 'valid'
        else:
            result['days_to_expiry'] = None
            result['expiry_status'] = 'permanent'
        return result

    def is_valid(self):
        """检查证书是否在有效期内"""
        if not self.expiry_date:
            return True
        return self.expiry_date >= datetime.now().date()

    def is_expiring_soon(self, days=30):
        """检查证书是否即将到期"""
        if not self.expiry_date:
            return False
        today = datetime.now().date()
        days_left = (self.expiry_date - today).days
        return 0 <= days_left <= days

    def __repr__(self):
        return f'<QualificationCertificate {self.certificate_number}>'


class PositionQualification(BaseModel):
    """岗位资质要求"""
    __tablename__ = 'position_qualification'

    position_name = db.Column(db.String(100), unique=True, nullable=False, comment='岗位名称')
    required_certificates = db.Column(db.Text, comment='所需证书类型列表(逗号分隔)')
    description = db.Column(db.Text, comment='岗位描述')

    def get_required_cert_list(self):
        """获取所需证书类型列表"""
        if not self.required_certificates:
            return []
        return [x.strip() for x in self.required_certificates.split(',') if x.strip()]

    def set_required_cert_list(self, cert_types):
        """设置所需证书类型列表"""
        if cert_types:
            self.required_certificates = ','.join(cert_types)
        else:
            self.required_certificates = None

    def to_dict(self):
        result = super().to_dict()
        result['certificate_list'] = self.get_required_cert_list()
        return result

    def __repr__(self):
        return f'<PositionQualification {self.position_name}>'
