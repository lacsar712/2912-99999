"""
生产线模型
"""
from database.db import db
from models.base import BaseModel


class ProductionLine(BaseModel):
    """生产线模型"""
    __tablename__ = 'production_line'

    line_code = db.Column(db.String(50), unique=True, nullable=False, comment='生产线编号')
    line_name = db.Column(db.String(100), nullable=False, comment='生产线名称')
    description = db.Column(db.Text, comment='生产线描述')
    status = db.Column(db.Enum('running', 'stopped', 'maintenance', 'error'), default='stopped', comment='状态')
    capacity = db.Column(db.Integer, default=0, comment='产能')
    location = db.Column(db.String(100), comment='位置')
    supervisor = db.Column(db.String(50), comment='负责人')

    # 关联
    equipments = db.relationship('Equipment', backref='production_line', lazy='dynamic')
    tasks = db.relationship('ProductionTask', backref='production_line', lazy='dynamic')

    def to_dict(self):
        result = super().to_dict()
        try:
            result['equipment_count'] = self.equipments.filter_by(status='running').count()
        except Exception:
            result['equipment_count'] = 0
        try:
            result['task_count'] = self.tasks.filter_by(status='in_progress').count()
        except Exception:
            result['task_count'] = 0
        return result

    def __repr__(self):
        return f'<ProductionLine {self.line_name}>'


class Equipment(BaseModel):
    """生产设备模型"""
    __tablename__ = 'equipment'

    equipment_code = db.Column(db.String(50), unique=True, nullable=False, comment='设备编号')
    equipment_name = db.Column(db.String(100), nullable=False, comment='设备名称')
    equipment_type = db.Column(db.String(50), comment='设备类型')
    line_id = db.Column(db.BigInteger, db.ForeignKey('production_line.id'), comment='所属生产线ID')
    status = db.Column(db.Enum('running', 'idle', 'maintenance', 'error', 'offline'), default='offline', comment='状态')
    model = db.Column(db.String(100), comment='型号')
    manufacturer = db.Column(db.String(100), comment='制造商')
    purchase_date = db.Column(db.Date, comment='购买日期')
    install_date = db.Column(db.Date, comment='安装日期')
    runtime_hours = db.Column(db.Numeric(10, 2), default=0, comment='运行时长(小时)')
    temperature = db.Column(db.Numeric(5, 2), comment='当前温度')
    pressure = db.Column(db.Numeric(7, 2), comment='当前压力')
    speed = db.Column(db.Numeric(8, 2), comment='运行速度')

    # 关联
    sensors = db.relationship('Sensor', backref='equipment', lazy='dynamic')

    def to_dict(self):
        result = super().to_dict()
        result['running_sensors'] = self.sensors.filter_by(status='normal').count()
        result['warning_sensors'] = self.sensors.filter_by(status='warning').count()
        return result

    def __repr__(self):
        return f'<Equipment {self.equipment_name}>'


class Sensor(BaseModel):
    """传感器模型"""
    __tablename__ = 'sensor'

    sensor_code = db.Column(db.String(50), unique=True, nullable=False, comment='传感器编号')
    sensor_name = db.Column(db.String(100), nullable=False, comment='传感器名称')
    sensor_type = db.Column(db.String(50), comment='传感器类型(温度/压力/湿度/速度等)')
    equipment_id = db.Column(db.BigInteger, db.ForeignKey('equipment.id'), comment='所属设备ID')
    unit = db.Column(db.String(20), comment='单位')
    min_value = db.Column(db.Numeric(10, 4), comment='最小值')
    max_value = db.Column(db.Numeric(10, 4), comment='最大值')
    threshold_low = db.Column(db.Numeric(10, 4), comment='告警阈值-低')
    threshold_high = db.Column(db.Numeric(10, 4), comment='告警阈值-高')
    status = db.Column(db.Enum('normal', 'warning', 'error', 'offline'), default='normal', comment='状态')
    last_value = db.Column(db.Numeric(10, 4), comment='最后读数')
    last_read_time = db.Column(db.DateTime, comment='最后读取时间')

    def check_threshold(self):
        """检查阈值"""
        if self.last_value is None:
            return 'offline'

        if self.threshold_low and self.last_value < self.threshold_low:
            return 'warning'
        if self.threshold_high and self.last_value > self.threshold_high:
            return 'warning'

        return 'normal'

    def __repr__(self):
        return f'<Sensor {self.sensor_name}>'


class ProductionTask(BaseModel):
    """生产任务模型"""
    __tablename__ = 'production_task'

    task_code = db.Column(db.String(50), unique=True, nullable=False, comment='任务编号')
    task_name = db.Column(db.String(100), nullable=False, comment='任务名称')
    line_id = db.Column(db.BigInteger, db.ForeignKey('production_line.id'), comment='生产线ID')
    product_name = db.Column(db.String(100), comment='产品名称')
    product_spec = db.Column(db.String(100), comment='产品规格')
    quantity = db.Column(db.Integer, comment='计划数量')
    completed_quantity = db.Column(db.Integer, default=0, comment='已完成数量')
    status = db.Column(db.Enum('pending', 'in_progress', 'paused', 'completed', 'cancelled'), default='pending', comment='状态')
    priority = db.Column(db.Integer, default=5, comment='优先级(1-10)')
    start_time = db.Column(db.DateTime, comment='计划开始时间')
    end_time = db.Column(db.DateTime, comment='计划结束时间')
    actual_start_time = db.Column(db.DateTime, comment='实际开始时间')
    actual_end_time = db.Column(db.DateTime, comment='实际结束时间')

    def get_progress(self):
        """获取进度百分比"""
        if self.quantity and self.quantity > 0:
            return round(self.completed_quantity / self.quantity * 100, 2)
        return 0

    def to_dict(self):
        result = super().to_dict()
        result['progress'] = self.get_progress()
        return result

    def __repr__(self):
        return f'<ProductionTask {self.task_name}>'


class ProductionRecord(BaseModel):
    """生产数据记录模型"""
    __tablename__ = 'production_record'

    equipment_id = db.Column(db.BigInteger, nullable=False, comment='设备ID')
    task_id = db.Column(db.BigInteger, comment='任务ID')
    product_count = db.Column(db.Integer, default=0, comment='生产数量')
    qualified_count = db.Column(db.Integer, default=0, comment='合格数量')
    defect_count = db.Column(db.Integer, default=0, comment='缺陷数量')
    yield_rate = db.Column(db.Numeric(5, 2), comment='良品率')
    temperature = db.Column(db.Numeric(5, 2), comment='平均温度')
    humidity = db.Column(db.Numeric(5, 2), comment='平均湿度')
    duration = db.Column(db.Integer, comment='运行时长(秒)')
    efficiency = db.Column(db.Numeric(5, 2), comment='生产效率')
    record_time = db.Column(db.DateTime, nullable=False, comment='记录时间')

    def __repr__(self):
        return f'<ProductionRecord {self.id}>'


class AlertRecord(BaseModel):
    """告警记录模型"""
    __tablename__ = 'alert_record'

    alert_code = db.Column(db.String(50), nullable=False, comment='告警编号')
    alert_type = db.Column(db.String(50), comment='告警类型')
    equipment_id = db.Column(db.BigInteger, comment='设备ID')
    sensor_id = db.Column(db.BigInteger, comment='传感器ID')
    severity = db.Column(db.Enum('info', 'warning', 'error', 'critical'), default='warning', comment='严重程度')
    message = db.Column(db.Text, comment='告警消息')
    value = db.Column(db.Numeric(10, 4), comment='告警值')
    threshold = db.Column(db.Numeric(10, 4), comment='阈值')
    status = db.Column(db.Enum('active', 'acknowledged', 'resolved'), default='active', comment='状态')
    resolved_time = db.Column(db.DateTime, comment='解决时间')
    resolve_note = db.Column(db.Text, comment='解决备注')

    def __repr__(self):
        return f'<AlertRecord {self.alert_code}>'
