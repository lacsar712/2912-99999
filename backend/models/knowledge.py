"""
知识库模型
"""
from datetime import datetime
from database.db import db
from models.base import BaseModel


class KnowledgeCategory(BaseModel):
    """知识分类模型"""
    __tablename__ = 'knowledge_category'

    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    parent_id = db.Column(db.BigInteger, default=0, comment='父分类ID，0为顶级')
    sort_order = db.Column(db.Integer, default=0, comment='排序号')
    description = db.Column(db.String(255), comment='分类描述')

    def to_dict(self):
        result = super().to_dict()
        return result

    @classmethod
    def get_tree(cls):
        """获取分类树"""
        categories = cls.query.filter(cls.status == 1).order_by(cls.sort_order.asc(), cls.id.asc()).all()
        cat_dict = {cat.id: {**cat.to_dict(), 'children': []} for cat in categories}
        
        tree = []
        for cat_id, cat_data in cat_dict.items():
            parent_id = cat_data.get('parent_id', 0)
            if parent_id == 0:
                tree.append(cat_data)
            else:
                if parent_id in cat_dict:
                    cat_dict[parent_id]['children'].append(cat_data)
        
        return tree

    @classmethod
    def get_by_parent(cls, parent_id=0):
        """根据父ID获取子分类"""
        return cls.query.filter(
            cls.parent_id == parent_id,
            cls.status == 1
        ).order_by(cls.sort_order.asc(), cls.id.asc()).all()

    @classmethod
    def get_all_descendant_ids(cls, category_id):
        """获取所有后代分类ID"""
        ids = [category_id]
        children = cls.query.filter(
            cls.parent_id == category_id,
            cls.status == 1
        ).all()
        for child in children:
            ids.extend(cls.get_all_descendant_ids(child.id))
        return ids


class KnowledgeDocument(BaseModel):
    """知识文档模型"""
    __tablename__ = 'knowledge_document'

    title = db.Column(db.String(200), nullable=False, comment='文档标题')
    category_id = db.Column(db.BigInteger, nullable=False, comment='所属分类ID')
    content = db.Column(db.Text, comment='正文Markdown')
    tags = db.Column(db.String(500), comment='标签列表，逗号分隔')
    version = db.Column(db.String(20), default='1.0', comment='版本号')
    doc_status = db.Column(db.String(20), default='draft', comment='状态：draft草稿/published发布/deprecated废弃')
    attachments = db.Column(db.Text, comment='附件base64数组JSON')
    view_count = db.Column(db.Integer, default=0, comment='查看次数')
    like_count = db.Column(db.Integer, default=0, comment='点赞数')
    author_id = db.Column(db.BigInteger, comment='作者ID')
    author_name = db.Column(db.String(50), comment='作者名称')
    summary = db.Column(db.String(500), comment='文档摘要')

    def to_dict(self):
        result = super().to_dict()
        if result.get('tags'):
            result['tags'] = [t.strip() for t in result['tags'].split(',') if t.strip()]
        else:
            result['tags'] = []
        return result

    @classmethod
    def search(cls, keyword, category_id=None, page=1, size=10, status=None):
        """全文搜索：标题/正文/tag模糊匹配"""
        query = cls.query.filter(cls.status == 1)
        
        if keyword:
            like_pattern = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    cls.title.like(like_pattern),
                    cls.content.like(like_pattern),
                    cls.tags.like(like_pattern)
                )
            )
        
        if category_id:
            cat_ids = KnowledgeCategory.get_all_descendant_ids(category_id)
            query = query.filter(cls.category_id.in_(cat_ids))
        
        if status:
            query = query.filter(cls.doc_status == status)
        else:
            query = query.filter(cls.doc_status == 'published')
        
        query = query.order_by(cls.update_time.desc())
        
        pagination = query.paginate(page=page, per_page=size, error_out=False)
        
        items = []
        for doc in pagination.items:
            doc_dict = doc.to_dict()
            doc_dict['highlight'] = cls._get_highlight_snippet(doc, keyword)
            items.append(doc_dict)
        
        return {
            'items': items,
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }

    @staticmethod
    def _get_highlight_snippet(doc, keyword, snippet_length=150):
        """获取高亮片段"""
        if not keyword:
            return ''
        
        text = doc.content or ''
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        idx = text_lower.find(keyword_lower)
        if idx == -1:
            return ''
        
        start = max(0, idx - snippet_length // 2)
        end = min(len(text), idx + len(keyword) + snippet_length // 2)
        
        snippet = text[start:end]
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'
        
        return snippet

    @classmethod
    def get_by_category(cls, category_id, page=1, size=10, status=None):
        """根据分类获取文档"""
        cat_ids = KnowledgeCategory.get_all_descendant_ids(category_id)
        query = cls.query.filter(
            cls.category_id.in_(cat_ids),
            cls.status == 1
        )
        
        if status:
            query = query.filter(cls.doc_status == status)
        
        query = query.order_by(cls.update_time.desc())
        
        pagination = query.paginate(page=page, per_page=size, error_out=False)
        return {
            'items': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }


class KnowledgeVersion(BaseModel):
    """文档版本历史模型"""
    __tablename__ = 'knowledge_version'

    doc_id = db.Column(db.BigInteger, nullable=False, comment='文档ID')
    version = db.Column(db.String(20), nullable=False, comment='版本号')
    title = db.Column(db.String(200), comment='标题')
    content = db.Column(db.Text, comment='正文Markdown')
    tags = db.Column(db.String(500), comment='标签列表')
    attachments = db.Column(db.Text, comment='附件base64数组JSON')
    summary = db.Column(db.String(500), comment='文档摘要')
    publisher_id = db.Column(db.BigInteger, comment='发布人ID')
    publisher_name = db.Column(db.String(50), comment='发布人名称')
    change_summary = db.Column(db.String(500), comment='变更摘要')
    publish_time = db.Column(db.DateTime, default=datetime.now, comment='发布时间')

    def to_dict(self):
        result = super().to_dict()
        if result.get('tags'):
            result['tags'] = [t.strip() for t in result['tags'].split(',') if t.strip()]
        else:
            result['tags'] = []
        return result

    @classmethod
    def get_by_doc(cls, doc_id):
        """获取文档的版本历史"""
        return cls.query.filter(
            cls.doc_id == doc_id,
            cls.status == 1
        ).order_by(cls.publish_time.desc()).all()


class KnowledgeComment(BaseModel):
    """文档评论模型"""
    __tablename__ = 'knowledge_comment'

    doc_id = db.Column(db.BigInteger, nullable=False, comment='文档ID')
    parent_id = db.Column(db.BigInteger, default=0, comment='父评论ID，0为顶级评论')
    content = db.Column(db.Text, comment='评论内容')
    commenter_id = db.Column(db.BigInteger, comment='评论人ID')
    commenter_name = db.Column(db.String(50), comment='评论人名称')
    reply_to_id = db.Column(db.BigInteger, comment='回复目标用户ID')
    reply_to_name = db.Column(db.String(50), comment='回复目标用户名称')
    like_count = db.Column(db.Integer, default=0, comment='点赞数')

    def to_dict(self):
        return super().to_dict()

    @classmethod
    def get_by_doc(cls, doc_id, page=1, size=20):
        """获取文档评论列表（只返回顶级评论，子评论另行获取）"""
        query = cls.query.filter(
            cls.doc_id == doc_id,
            cls.parent_id == 0,
            cls.status == 1
        ).order_by(cls.create_time.desc())
        
        pagination = query.paginate(page=page, per_page=size, error_out=False)
        
        items = []
        for comment in pagination.items:
            comment_dict = comment.to_dict()
            comment_dict['replies'] = cls._get_replies(comment.id)
            items.append(comment_dict)
        
        return {
            'items': items,
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }

    @classmethod
    def _get_replies(cls, parent_id):
        """获取子评论（楼中楼）"""
        replies = cls.query.filter(
            cls.parent_id == parent_id,
            cls.status == 1
        ).order_by(cls.create_time.asc()).all()
        return [r.to_dict() for r in replies]


class KnowledgeLike(BaseModel):
    """文档点赞记录模型"""
    __tablename__ = 'knowledge_like'

    doc_id = db.Column(db.BigInteger, nullable=False, comment='文档ID')
    user_id = db.Column(db.BigInteger, nullable=False, comment='用户ID')
    user_name = db.Column(db.String(50), comment='用户名称')

    def to_dict(self):
        return super().to_dict()

    @classmethod
    def has_liked(cls, doc_id, user_id):
        """检查用户是否已点赞"""
        return cls.query.filter(
            cls.doc_id == doc_id,
            cls.user_id == user_id,
            cls.status == 1
        ).first() is not None
