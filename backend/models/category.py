"""
分类模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel


class Category(BaseModel):
    """分类模型"""
    __tablename__ = 't_category'

    name = db.Column(db.String(50), nullable=False, comment='分类名称')
    parent_id = db.Column(db.BigInteger, default=0, comment='父分类ID')
    sort_order = db.Column(db.Integer, default=0, comment='排序')

    @staticmethod
    def get_tree():
        """获取分类树"""
        categories = Category.query.filter(
            Category.status == 1
        ).order_by(Category.sort_order).all()

        # 构建树形结构
        category_dict = {c.id: c.to_dict() for c in categories}
        tree = []

        for category in categories:
            if category.parent_id == 0:
                category_dict[category.id]['children'] = []
                tree.append(category_dict[category.id])
            else:
                parent = category_dict.get(category.parent_id)
                if parent:
                    if 'children' not in parent:
                        parent['children'] = []
                    parent['children'].append(category_dict[category.id])

        return tree

    def __repr__(self):
        return f'<Category {self.name}>'
