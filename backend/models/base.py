"""
基础模型
"""
from datetime import datetime
from database.db import db


class BaseModel(db.Model):
    """基础模型类"""
    __abstract__ = True

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    status = db.Column(db.SmallInteger, default=1, comment='状态: 0删除/1正常')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            result[column.name] = value
        return result

    def save(self):
        """保存模型"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """删除模型（软删除）"""
        self.status = 0
        db.session.commit()
        return self

    def update(self, **kwargs):
        """更新模型"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    @classmethod
    def get_by_id(cls, id):
        """根据ID获取"""
        # 检查status字段类型，如果是整数型则过滤status=1（未删除）
        status_col = cls.__table__.columns.get('status')
        if status_col is not None:
            # 检查是否是整数类型（SmallInteger 或 Integer）
            col_type_name = type(status_col.type).__name__
            if col_type_name in ('SmallInteger', 'Integer'):
                return cls.query.filter(cls.id == id, cls.status == 1).first()
        # 枚举类型或其他类型，直接根据ID查询
        return cls.query.filter(cls.id == id).first()

    @classmethod
    def get_all(cls):
        """获取所有"""
        # 检查status字段类型
        status_col = cls.__table__.columns.get('status')
        if status_col is not None:
            col_type_name = type(status_col.type).__name__
            if col_type_name in ('SmallInteger', 'Integer'):
                return cls.query.filter(cls.status == 1).all()
        # 枚举类型，返回所有
        return cls.query.all()

    @classmethod
    def get_page(cls, page=1, size=10):
        """分页查询"""
        # 检查status字段类型
        status_col = cls.__table__.columns.get('status')
        query = cls.query
        if status_col is not None:
            col_type_name = type(status_col.type).__name__
            if col_type_name in ('SmallInteger', 'Integer'):
                query = query.filter(cls.status == 1)
        
        pagination = query.paginate(
            page=page,
            per_page=size,
            error_out=False
        )
        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }
