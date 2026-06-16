"""
不合格品处置模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel
from models.user import User


class DisposalOrder(BaseModel):
    """待处置单模型"""
    __tablename__ = 'disposal_order'

    order_code = db.Column(db.String(50), unique=True, nullable=False, comment='处置单号')
    source_type = db.Column(db.Enum('quality_check', 'inspection', 'manual'), default='manual', comment='来源:质检不合格/巡检/手工录入')
    source_id = db.Column(db.BigInteger, comment='来源记录ID')
    source_code = db.Column(db.String(50), comment='来源记录编号')

    related_type = db.Column(db.Enum('product', 'equipment'), comment='关联类型:产品/设备')
    related_id = db.Column(db.BigInteger, comment='关联产品或设备ID')
    related_code = db.Column(db.String(50), comment='关联产品或设备编号')
    related_name = db.Column(db.String(100), comment='关联产品或设备名称')

    quantity = db.Column(db.Integer, default=1, comment='数量')
    unit = db.Column(db.String(20), comment='单位')
    unit_price = db.Column(db.Numeric(10, 2), default=0, comment='单价')
    defect_description = db.Column(db.Text, comment='缺陷描述')

    suggested_disposal = db.Column(db.Enum('rework', 'concession', 'scrap'), comment='处置建议:返工/让步接收/报废')

    applicant_id = db.Column(db.BigInteger, comment='申请人ID')
    applicant = db.Column(db.String(50), comment='申请人')
    apply_time = db.Column(db.DateTime, default=datetime.now, comment='申请时间')

    current_approval_level = db.Column(db.SmallInteger, default=0, comment='当前审批级别:0待提交/1班组长/2部门主管')
    status = db.Column(db.Enum(
        'draft', 'pending_approval', 'approved', 'rejected', 'returned', 'processing', 'completed'
    ), default='draft', comment='状态:草稿/待审批/已通过/已驳回/已退回/处理中/已完成')

    attachment = db.Column(db.Text, comment='附件base64')
    remark = db.Column(db.Text, comment='备注')

    approvals = db.relationship('DisposalApproval', backref='disposal_order', lazy='dynamic', cascade='all, delete-orphan')
    result = db.relationship('DisposalResult', backref='disposal_order', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        result = super().to_dict()
        result['approval_list'] = [a.to_dict() for a in self.approvals.order_by(DisposalApproval.create_time.asc()).all()]
        if self.result:
            result['disposal_result'] = self.result.to_dict()
        return result

    def __repr__(self):
        return f'<DisposalOrder {self.order_code}>'


class DisposalApproval(BaseModel):
    """审批记录模型"""
    __tablename__ = 'disposal_approval'

    disposal_order_id = db.Column(db.BigInteger, db.ForeignKey('disposal_order.id'), nullable=False, comment='处置单ID')
    approval_level = db.Column(db.SmallInteger, comment='审批级别:1班组长/2部门主管')
    approval_role = db.Column(db.String(20), comment='审批角色')

    approver_id = db.Column(db.BigInteger, comment='审批人ID')
    approver = db.Column(db.String(50), comment='审批人')
    approval_time = db.Column(db.DateTime, comment='审批时间')

    action = db.Column(db.Enum('approve', 'reject', 'return'), comment='审批动作:通过/驳回/退回')
    opinion = db.Column(db.Text, comment='审批意见')

    def to_dict(self):
        result = super().to_dict()
        result.pop('disposal_order_id', None)
        return result

    def __repr__(self):
        return f'<DisposalApproval {self.id}>'


class DisposalResult(BaseModel):
    """处置结果模型"""
    __tablename__ = 'disposal_result'

    disposal_order_id = db.Column(db.BigInteger, db.ForeignKey('disposal_order.id'), unique=True, nullable=False, comment='处置单ID')

    final_decision = db.Column(db.Enum('rework', 'concession', 'scrap'), comment='最终决定:返工/让步接收/报废')

    operator_id = db.Column(db.BigInteger, comment='操作人ID')
    operator = db.Column(db.String(50), comment='操作人')
    operate_time = db.Column(db.DateTime, default=datetime.now, comment='操作时间')

    loss_estimate = db.Column(db.Numeric(12, 2), default=0, comment='损失估算')
    operation_record = db.Column(db.Text, comment='操作记录')
    remark = db.Column(db.Text, comment='备注')

    def to_dict(self):
        result = super().to_dict()
        result.pop('disposal_order_id', None)
        return result

    def __repr__(self):
        return f'<DisposalResult {self.id}>'
