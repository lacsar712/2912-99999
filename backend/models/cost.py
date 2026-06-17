"""
成本核算模型
"""
from database.db import db
from models.base import BaseModel


class CostElement(BaseModel):
    """成本要素字典模型"""
    __tablename__ = 'cost_element'

    element_code = db.Column(db.String(50), unique=True, nullable=False, comment='要素编码')
    element_name = db.Column(db.String(100), nullable=False, comment='要素名称')
    element_type = db.Column(db.Enum('material', 'labor', 'depreciation', 'energy', 'other'), default='other', comment='要素类型: material原材料/labor人工/depreciation设备折旧/energy能源/other其他')
    unit = db.Column(db.String(20), comment='计量单位')
    price = db.Column(db.Numeric(12, 2), default=0, comment='单价(元)')
    description = db.Column(db.Text, comment='描述')
    sort_order = db.Column(db.Integer, default=0, comment='排序')

    def to_dict(self):
        result = super().to_dict()
        result['price'] = float(result['price']) if result['price'] else 0
        return result

    def __repr__(self):
        return f'<CostElement {self.element_name}>'


class CostRecord(BaseModel):
    """成本登记模型"""
    __tablename__ = 'cost_record'

    record_code = db.Column(db.String(50), unique=True, nullable=False, comment='登记编号')
    task_id = db.Column(db.BigInteger, db.ForeignKey('production_task.id'), comment='关联生产任务ID')
    element_id = db.Column(db.BigInteger, db.ForeignKey('cost_element.id'), comment='成本要素ID')
    quantity = db.Column(db.Numeric(12, 2), default=0, comment='数量')
    unit_price = db.Column(db.Numeric(12, 2), default=0, comment='单价(元)')
    amount = db.Column(db.Numeric(12, 2), default=0, comment='总金额(元)')
    remark = db.Column(db.Text, comment='备注')
    register_by = db.Column(db.String(50), comment='登记人')
    record_date = db.Column(db.Date, comment='登记日期')
    source = db.Column(db.Enum('manual', 'auto'), default='manual', comment='来源: manual手工/auto自动折算')

    element = db.relationship('CostElement', backref='records')
    task = db.relationship('ProductionTask', backref='cost_records')

    def to_dict(self):
        result = super().to_dict()
        result['quantity'] = float(result['quantity']) if result['quantity'] else 0
        result['unit_price'] = float(result['unit_price']) if result['unit_price'] else 0
        result['amount'] = float(result['amount']) if result['amount'] else 0
        if self.element:
            result['element_name'] = self.element.element_name
            result['element_type'] = self.element.element_type
            result['element_code'] = self.element.element_code
            result['unit'] = self.element.unit
        if self.task:
            result['task_code'] = self.task.task_code
            result['task_name'] = self.task.task_name
            result['product_name'] = self.task.product_name
            result['line_id'] = self.task.line_id
        return result

    def __repr__(self):
        return f'<CostRecord {self.record_code}>'


class CostSummary(BaseModel):
    """成本汇总模型（任务级）"""
    __tablename__ = 'cost_summary'

    task_id = db.Column(db.BigInteger, db.ForeignKey('production_task.id'), unique=True, comment='生产任务ID')
    total_material = db.Column(db.Numeric(12, 2), default=0, comment='原材料总成本')
    total_labor = db.Column(db.Numeric(12, 2), default=0, comment='人工总成本')
    total_depreciation = db.Column(db.Numeric(12, 2), default=0, comment='设备折旧总成本')
    total_energy = db.Column(db.Numeric(12, 2), default=0, comment='能源总成本')
    total_other = db.Column(db.Numeric(12, 2), default=0, comment='其他总成本')
    total_amount = db.Column(db.Numeric(12, 2), default=0, comment='总成本')
    unit_cost = db.Column(db.Numeric(12, 4), default=0, comment='单位成本')
    auto_calculated = db.Column(db.Boolean, default=False, comment='是否自动计算')
    missing_elements = db.Column(db.Text, comment='缺失的要素(提示用户补录)')

    task = db.relationship('ProductionTask', backref='cost_summary')

    def to_dict(self):
        result = super().to_dict()
        result['total_material'] = float(result['total_material']) if result['total_material'] else 0
        result['total_labor'] = float(result['total_labor']) if result['total_labor'] else 0
        result['total_depreciation'] = float(result['total_depreciation']) if result['total_depreciation'] else 0
        result['total_energy'] = float(result['total_energy']) if result['total_energy'] else 0
        result['total_other'] = float(result['total_other']) if result['total_other'] else 0
        result['total_amount'] = float(result['total_amount']) if result['total_amount'] else 0
        result['unit_cost'] = float(result['unit_cost']) if result['unit_cost'] else 0
        if self.task:
            result['task_code'] = self.task.task_code
            result['task_name'] = self.task.task_name
            result['product_name'] = self.task.product_name
            result['quantity'] = self.task.quantity
            result['line_id'] = self.task.line_id
        return result

    def __repr__(self):
        return f'<CostSummary task_id={self.task_id}>'
