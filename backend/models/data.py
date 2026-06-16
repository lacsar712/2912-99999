"""
数据模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel


class Data(BaseModel):
    """数据模型"""
    __tablename__ = 't_data'

    name = db.Column(db.String(100), nullable=False, comment='数据名称')
    type = db.Column(db.String(50), nullable=False, comment='数据类型')
    value = db.Column(db.Text, comment='数据值')
    description = db.Column(db.Text, comment='描述')
    category_id = db.Column(db.BigInteger, comment='分类ID')
    user_id = db.Column(db.BigInteger, nullable=False, comment='创建用户ID')

    # 关联关系
    # category = db.relationship('Category', backref='datas')
    # user = db.relationship('User', backref='datas')

    @staticmethod
    def search(keyword=None, type=None, category_id=None, user_id=None):
        """搜索数据"""
        query = Data.query.filter(Data.status == 1)

        if keyword:
            query = query.filter(
                db.or_(
                    Data.name.like(f'%{keyword}%'),
                    Data.description.like(f'%{keyword}%')
                )
            )

        if type:
            query = query.filter(Data.type == type)

        if category_id:
            query = query.filter(Data.category_id == category_id)

        if user_id:
            query = query.filter(Data.user_id == user_id)

        return query.order_by(Data.create_time.desc())

    def __repr__(self):
        return f'<Data {self.name}>'
