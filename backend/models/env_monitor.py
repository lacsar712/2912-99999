"""
环境监测模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel
import json


class EnvArea(BaseModel):
    """区域字典 - 支持多层级（车间/仓库/办公区等）"""
    __tablename__ = 'env_area'

    area_code = db.Column(db.String(50), unique=True, nullable=False, comment='区域编码')
    area_name = db.Column(db.String(100), nullable=False, comment='区域名称')
    parent_id = db.Column(db.BigInteger, db.ForeignKey('env_area.id'), nullable=True, comment='父区域ID')
    area_type = db.Column(db.String(50), comment='区域类型: workshop/warehouse/office/other')
    description = db.Column(db.Text, comment='区域描述')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    parent = db.relationship(
        'EnvArea',
        remote_side=lambda: EnvArea.id,
        foreign_keys=lambda: [EnvArea.parent_id],
        backref=db.backref('children', lazy='dynamic'),
        lazy='joined'
    )

    def to_dict(self):
        result = super().to_dict()
        result['children'] = [child.to_dict() for child in self.children if child.status == 1] if self.children else []
        result['parent_name'] = self.parent.area_name if self.parent else ''
        return result

    def __repr__(self):
        return f'<EnvArea {self.area_name}>'


class EnvMonitorPoint(BaseModel):
    """环境监测点"""
    __tablename__ = 'env_monitor_point'

    point_code = db.Column(db.String(50), unique=True, nullable=False, comment='监测点编号')
    point_name = db.Column(db.String(100), nullable=False, comment='监测点名称')
    area_id = db.Column(db.BigInteger, db.ForeignKey('env_area.id'), nullable=False, comment='关联区域ID')
    monitor_items = db.Column(db.Text, comment='监测项目列表JSON: [{"name": "温度", "unit": "°C"}, ...]')
    point_status = db.Column(db.Enum('active', 'inactive', 'maintenance'), default='active', comment='监测点状态')
    location = db.Column(db.String(200), comment='具体位置描述')
    description = db.Column(db.Text, comment='备注')

    area = db.relationship('EnvArea', backref='monitor_points', lazy='joined')

    def get_monitor_items(self):
        """获取监测项目列表"""
        if self.monitor_items:
            try:
                return json.loads(self.monitor_items)
            except Exception:
                return []
        return []

    def set_monitor_items(self, items):
        """设置监测项目列表"""
        self.monitor_items = json.dumps(items, ensure_ascii=False)

    def to_dict(self):
        result = super().to_dict()
        result['monitor_items'] = self.get_monitor_items()
        result['area_name'] = self.area.area_name if self.area else ''
        result['area_code'] = self.area.area_code if self.area else ''
        return result

    def __repr__(self):
        return f'<EnvMonitorPoint {self.point_name}>'


class EnvReading(BaseModel):
    """环境监测读数"""
    __tablename__ = 'env_reading'

    point_id = db.Column(db.BigInteger, db.ForeignKey('env_monitor_point.id'), nullable=False, comment='监测点ID')
    item_name = db.Column(db.String(50), nullable=False, comment='监测项目名称')
    item_value = db.Column(db.Numeric(12, 4), nullable=False, comment='监测值')
    item_unit = db.Column(db.String(20), comment='单位')
    read_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='读数时间')
    is_normal = db.Column(db.Boolean, default=True, comment='是否正常')

    point = db.relationship('EnvMonitorPoint', backref='readings', lazy='joined')

    def to_dict(self):
        result = super().to_dict()
        result['point_name'] = self.point.point_name if self.point else ''
        result['point_code'] = self.point.point_code if self.point else ''
        result['area_id'] = self.point.area_id if self.point else None
        return result

    def __repr__(self):
        return f'<EnvReading {self.item_name}: {self.item_value}{self.item_unit}>'


class EnvStandard(BaseModel):
    """环境标准 - 项目的安全阈值上下限与告警阈值"""
    __tablename__ = 'env_standard'

    item_name = db.Column(db.String(50), unique=True, nullable=False, comment='监测项目名称')
    item_unit = db.Column(db.String(20), comment='单位')
    safety_low = db.Column(db.Numeric(12, 4), comment='安全阈值下限')
    safety_high = db.Column(db.Numeric(12, 4), comment='安全阈值上限')
    alert_low = db.Column(db.Numeric(12, 4), comment='告警阈值下限')
    alert_high = db.Column(db.Numeric(12, 4), comment='告警阈值上限')
    severity = db.Column(db.Enum('info', 'warning', 'error', 'critical'), default='warning', comment='超限告警级别')
    description = db.Column(db.Text, comment='标准说明')

    def check_value(self, value):
        """
        检查数值是否在安全范围内
        返回: ('normal'|'warning'|'danger', 超限说明)
        """
        if value is None:
            return ('offline', '无数据')
        
        # 先检查告警阈值
        if self.alert_low is not None and value < self.alert_low:
            return ('danger', f'{value} 低于告警下限 {self.alert_low}')
        if self.alert_high is not None and value > self.alert_high:
            return ('danger', f'{value} 高于告警上限 {self.alert_high}')
        
        # 再检查安全阈值
        if self.safety_low is not None and value < self.safety_low:
            return ('warning', f'{value} 接近安全下限 {self.safety_low}')
        if self.safety_high is not None and value > self.safety_high:
            return ('warning', f'{value} 接近安全上限 {self.safety_high}')
        
        return ('normal', '正常')

    def __repr__(self):
        return f'<EnvStandard {self.item_name}>'
