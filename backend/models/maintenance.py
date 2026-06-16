"""
维修工单模型
"""
from database.db import db
from models.base import BaseModel


class MaintenanceWorkOrder(BaseModel):
    """维修工单模型"""
    __tablename__ = 'maintenance_work_order'

    order_code = db.Column(db.String(50), unique=True, nullable=False, comment='工单编号')
    order_name = db.Column(db.String(200), nullable=False, comment='工单名称')
    equipment_id = db.Column(db.BigInteger, db.ForeignKey('equipment.id'), comment='关联设备ID')
    equipment_type = db.Column(db.String(50), comment='设备类型')
    fault_description = db.Column(db.Text, comment='故障描述')
    work_type = db.Column(db.String(20), comment='维修类型: corrective/ predictive/ preventive')
    priority = db.Column(db.Enum('low', 'medium', 'high', 'critical'), default='medium', comment='优先级')
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'cancelled'), default='pending', comment='状态')
    assigned_to = db.Column(db.String(50), comment='负责人')
    plan_start_time = db.Column(db.DateTime, comment='计划开始时间')
    plan_end_time = db.Column(db.DateTime, comment='计划结束时间')
    actual_start_time = db.Column(db.DateTime, comment='实际开始时间')
    actual_end_time = db.Column(db.DateTime, comment='实际结束时间')
    work_content = db.Column(db.Text, comment='维修内容')
    materials = db.Column(db.Text, comment='耗材明细(JSON)')
    materials_cost = db.Column(db.Numeric(10, 2), default=0, comment='耗材费用')
    labor_cost = db.Column(db.Numeric(10, 2), default=0, comment='人工费用')
    total_cost = db.Column(db.Numeric(10, 2), default=0, comment='总费用')
    remark = db.Column(db.Text, comment='备注')

    spare_usage = db.relationship('SpareOutbound', backref='work_order', lazy='dynamic')

    def to_dict(self):
        result = super().to_dict()
        try:
            if self.equipment_id:
                from models.production import Equipment
                equipment = Equipment.get_by_id(self.equipment_id)
                if equipment:
                    result['equipment_name'] = equipment.equipment_name
                    result['equipment_code'] = equipment.equipment_code
        except Exception:
            pass
        try:
            result['spare_count'] = self.spare_usage.count()
        except Exception:
            result['spare_count'] = 0
        return result

    def __repr__(self):
        return f'<MaintenanceWorkOrder {self.order_code}>'
