"""
备件库存模型
"""
from database.db import db
from models.base import BaseModel


class SparePart(BaseModel):
    """备件档案模型"""
    __tablename__ = 'spare_part'

    part_code = db.Column(db.String(50), unique=True, nullable=False, comment='备件编号')
    part_name = db.Column(db.String(100), nullable=False, comment='备件名称')
    specification = db.Column(db.String(200), comment='规格')
    unit = db.Column(db.String(20), comment='单位')
    safety_stock = db.Column(db.Integer, default=0, comment='安全库存')
    current_stock = db.Column(db.Integer, default=0, comment='当前库存')
    equipment_type = db.Column(db.String(50), comment='关联设备类型')
    equipment_id = db.Column(db.BigInteger, db.ForeignKey('equipment.id'), comment='关联具体设备ID')
    unit_price = db.Column(db.Numeric(10, 2), default=0, comment='单价')
    location = db.Column(db.String(100), comment='所在库位')
    remark = db.Column(db.Text, comment='备注')

    inbound_records = db.relationship('SpareInbound', backref='spare_part', lazy='dynamic')
    outbound_records = db.relationship('SpareOutbound', backref='spare_part', lazy='dynamic')
    inventory_records = db.relationship('SpareInventory', backref='spare_part', lazy='dynamic')

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
        result['is_low_stock'] = self.current_stock <= self.safety_stock
        return result

    def __repr__(self):
        return f'<SparePart {self.part_name}>'


class SpareInbound(BaseModel):
    """备件入库模型"""
    __tablename__ = 'spare_inbound'

    inbound_code = db.Column(db.String(50), unique=True, nullable=False, comment='入库单号')
    spare_part_id = db.Column(db.BigInteger, db.ForeignKey('spare_part.id'), nullable=False, comment='备件ID')
    source_type = db.Column(db.Enum('purchase', 'return'), default='purchase', comment='来源: purchase采购入库/return退库')
    batch_no = db.Column(db.String(50), comment='批次号')
    quantity = db.Column(db.Integer, nullable=False, comment='入库数量')
    unit_price = db.Column(db.Numeric(10, 2), default=0, comment='单价')
    total_price = db.Column(db.Numeric(10, 2), default=0, comment='总价')
    operator = db.Column(db.String(50), comment='操作人')
    inbound_time = db.Column(db.DateTime, comment='入库时间')
    remark = db.Column(db.Text, comment='备注')

    def to_dict(self):
        result = super().to_dict()
        try:
            if self.spare_part:
                result['part_code'] = self.spare_part.part_code
                result['part_name'] = self.spare_part.part_name
                result['specification'] = self.spare_part.specification
                result['unit'] = self.spare_part.unit
        except Exception:
            pass
        return result

    def __repr__(self):
        return f'<SpareInbound {self.inbound_code}>'


class SpareOutbound(BaseModel):
    """备件领用模型"""
    __tablename__ = 'spare_outbound'

    outbound_code = db.Column(db.String(50), unique=True, nullable=False, comment='领用单号')
    spare_part_id = db.Column(db.BigInteger, db.ForeignKey('spare_part.id'), nullable=False, comment='备件ID')
    work_order_id = db.Column(db.BigInteger, db.ForeignKey('maintenance_work_order.id'), comment='关联维修工单ID')
    reason = db.Column(db.String(200), comment='领用原因/自定义原因')
    receiver = db.Column(db.String(50), comment='领用人')
    quantity = db.Column(db.Integer, nullable=False, comment='领用数量')
    outbound_time = db.Column(db.DateTime, comment='领用时间')
    is_returned = db.Column(db.SmallInteger, default=0, comment='是否归还: 0否/1是')
    return_time = db.Column(db.DateTime, comment='归还时间')
    operator = db.Column(db.String(50), comment='操作人')
    remark = db.Column(db.Text, comment='备注')

    def to_dict(self):
        result = super().to_dict()
        try:
            if self.spare_part:
                result['part_code'] = self.spare_part.part_code
                result['part_name'] = self.spare_part.part_name
                result['specification'] = self.spare_part.specification
                result['unit'] = self.spare_part.unit
                result['unit_price'] = float(self.spare_part.unit_price) if self.spare_part.unit_price else 0
                result['total_price'] = float(self.spare_part.unit_price) * self.quantity if self.spare_part.unit_price else 0
        except Exception:
            pass
        try:
            if self.work_order_id:
                from models.maintenance import MaintenanceWorkOrder
                order = MaintenanceWorkOrder.get_by_id(self.work_order_id)
                if order:
                    result['order_code'] = order.order_code
                    result['order_name'] = order.order_name
        except Exception:
            pass
        return result

    def __repr__(self):
        return f'<SpareOutbound {self.outbound_code}>'


class SpareInventory(BaseModel):
    """月度盘点模型"""
    __tablename__ = 'spare_inventory'

    inventory_code = db.Column(db.String(50), unique=True, nullable=False, comment='盘点单号')
    spare_part_id = db.Column(db.BigInteger, db.ForeignKey('spare_part.id'), nullable=False, comment='备件ID')
    inventory_month = db.Column(db.String(7), nullable=False, comment='盘点月份 YYYY-MM')
    book_stock = db.Column(db.Integer, default=0, comment='账面库存')
    actual_stock = db.Column(db.Integer, default=0, comment='实物库存')
    difference = db.Column(db.Integer, default=0, comment='差异数量')
    difference_reason = db.Column(db.Text, comment='差异原因')
    operator = db.Column(db.String(50), comment='盘点人')
    inventory_time = db.Column(db.DateTime, comment='盘点时间')
    remark = db.Column(db.Text, comment='备注')

    def to_dict(self):
        result = super().to_dict()
        try:
            if self.spare_part:
                result['part_code'] = self.spare_part.part_code
                result['part_name'] = self.spare_part.part_name
                result['specification'] = self.spare_part.specification
                result['unit'] = self.spare_part.unit
        except Exception:
            pass
        return result

    def __repr__(self):
        return f'<SpareInventory {self.inventory_code}>'
