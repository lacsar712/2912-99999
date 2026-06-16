"""
知识库服务模块
"""
import json
from datetime import datetime
from database.db import db
from models.knowledge import (
    KnowledgeCategory,
    KnowledgeDocument,
    KnowledgeVersion,
    KnowledgeComment,
    KnowledgeLike
)
from utils.response import Response
from utils.validator import Validator


class KnowledgeService:
    """知识库服务类"""

    # ==================== 分类管理 ====================

    @staticmethod
    def get_category_tree():
        """获取分类树"""
        tree = KnowledgeCategory.get_tree()
        return Response.success(tree)

    @staticmethod
    def get_category(category_id):
        """获取分类详情"""
        category = KnowledgeCategory.get_by_id(category_id)
        if not category:
            return Response.not_found('分类不存在')
        return Response.success(category.to_dict())

    @staticmethod
    def create_category(data):
        """创建分类"""
        validation = Validator.validate_form(data, {
            'name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        parent_id = data.get('parent_id', 0)
        if parent_id:
            parent = KnowledgeCategory.get_by_id(parent_id)
            if not parent:
                return Response.bad_request('父分类不存在')

        category = KnowledgeCategory(
            name=data['name'],
            parent_id=parent_id,
            sort_order=data.get('sort_order', 0),
            description=data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        return Response.created(category.to_dict())

    @staticmethod
    def update_category(category_id, data):
        """更新分类"""
        category = KnowledgeCategory.get_by_id(category_id)
        if not category:
            return Response.not_found('分类不存在')

        if 'parent_id' in data and data['parent_id']:
            if data['parent_id'] == category_id:
                return Response.bad_request('不能将自己设为父分类')
            parent = KnowledgeCategory.get_by_id(data['parent_id'])
            if not parent:
                return Response.bad_request('父分类不存在')

        for key in ['name', 'parent_id', 'sort_order', 'description']:
            if key in data:
                setattr(category, key, data[key])

        db.session.commit()
        return Response.success(category.to_dict())

    @staticmethod
    def delete_category(category_id):
        """删除分类"""
        category = KnowledgeCategory.get_by_id(category_id)
        if not category:
            return Response.not_found('分类不存在')

        children = KnowledgeCategory.get_by_parent(category_id)
        if children:
            return Response.bad_request('该分类下还有子分类，无法删除')

        docs = KnowledgeDocument.query.filter_by(
            category_id=category_id,
            status=1
        ).first()
        if docs:
            return Response.bad_request('该分类下还有文档，无法删除')

        category.delete()
        return Response.success(message='删除成功')

    # ==================== 文档管理 ====================

    @staticmethod
    def get_documents(category_id=None, page=1, size=10, status=None, keyword=None):
        """获取文档列表"""
        if keyword:
            result = KnowledgeDocument.search(keyword, category_id, page, size, status)
        elif category_id:
            result = KnowledgeDocument.get_by_category(category_id, page, size, status)
        else:
            query = KnowledgeDocument.query.filter(KnowledgeDocument.status == 1)
            if status:
                query = query.filter(KnowledgeDocument.doc_status == status)
            query = query.order_by(KnowledgeDocument.update_time.desc())
            pagination = query.paginate(page=page, per_page=size, error_out=False)
            result = {
                'items': [item.to_dict() for item in pagination.items],
                'total': pagination.total,
                'page': page,
                'size': size,
                'pages': pagination.pages
            }

        return Response.paginate(
            result['items'],
            result['total'],
            result['page'],
            result['size']
        )

    @staticmethod
    def get_document(doc_id, user_id=None):
        """获取文档详情"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        doc_dict = doc.to_dict()
        if user_id:
            doc_dict['has_liked'] = KnowledgeLike.has_liked(doc_id, user_id)

        return Response.success(doc_dict)

    @staticmethod
    def create_document(data, user_id=None, user_name=None):
        """创建文档"""
        validation = Validator.validate_form(data, {
            'title': ['required'],
            'category_id': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        category = KnowledgeCategory.get_by_id(data['category_id'])
        if not category:
            return Response.bad_request('分类不存在')

        tags = data.get('tags', [])
        if isinstance(tags, list):
            tags_str = ','.join(tags)
        else:
            tags_str = tags or ''

        attachments = data.get('attachments', [])
        if attachments:
            attachments_str = json.dumps(attachments, ensure_ascii=False)
        else:
            attachments_str = None

        doc = KnowledgeDocument(
            title=data['title'],
            category_id=data['category_id'],
            content=data.get('content', ''),
            tags=tags_str,
            version=data.get('version', '1.0'),
            doc_status=data.get('doc_status', 'draft'),
            attachments=attachments_str,
            author_id=user_id,
            author_name=user_name,
            summary=data.get('summary', '')
        )
        db.session.add(doc)
        db.session.commit()

        if data.get('doc_status') == 'published':
            KnowledgeService._create_version(doc, data.get('change_summary', '初始版本'), user_id, user_name)

        return Response.created(doc.to_dict())

    @staticmethod
    def update_document(doc_id, data, user_id=None, user_name=None):
        """更新文档"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        if 'category_id' in data:
            category = KnowledgeCategory.get_by_id(data['category_id'])
            if not category:
                return Response.bad_request('分类不存在')

        if 'tags' in data:
            tags = data['tags']
            if isinstance(tags, list):
                doc.tags = ','.join(tags)
            else:
                doc.tags = tags or ''

        if 'attachments' in data:
            attachments = data['attachments']
            if attachments:
                doc.attachments = json.dumps(attachments, ensure_ascii=False)
            else:
                doc.attachments = None

        for key in ['title', 'category_id', 'content', 'version', 'doc_status', 'summary']:
            if key in data:
                setattr(doc, key, data[key])

        db.session.commit()

        if data.get('doc_status') == 'published' and doc.doc_status == 'published':
            change_summary = data.get('change_summary', '更新文档')
            KnowledgeService._create_version(doc, change_summary, user_id, user_name)

        return Response.success(doc.to_dict())

    @staticmethod
    def delete_document(doc_id):
        """删除文档"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')
        doc.delete()
        return Response.success(message='删除成功')

    # ==================== 发布与版本管理 ====================

    @staticmethod
    def publish_document(doc_id, data, user_id=None, user_name=None):
        """发布文档"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        change_summary = data.get('change_summary', '发布文档')
        new_version = data.get('version')

        if new_version:
            doc.version = new_version

        doc.doc_status = 'published'
        db.session.commit()

        KnowledgeService._create_version(doc, change_summary, user_id, user_name)

        return Response.success(doc.to_dict())

    @staticmethod
    def get_version_history(doc_id):
        """获取版本历史"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        versions = KnowledgeVersion.get_by_doc(doc_id)
        return Response.success([v.to_dict() for v in versions])

    @staticmethod
    def rollback_version(doc_id, version_id, user_id=None, user_name=None):
        """版本回滚"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        version = KnowledgeVersion.get_by_id(version_id)
        if not version or version.doc_id != doc_id:
            return Response.not_found('版本不存在')

        old_version = doc.version
        doc.title = version.title
        doc.content = version.content
        doc.tags = version.tags
        doc.attachments = version.attachments
        doc.summary = version.summary
        doc.version = version.version

        db.session.commit()

        KnowledgeService._create_version(
            doc,
            f'回滚到版本 {version.version}（原版本 {old_version}）',
            user_id,
            user_name
        )

        return Response.success(doc.to_dict())

    @staticmethod
    def _create_version(doc, change_summary, user_id=None, user_name=None):
        """创建版本记录"""
        version = KnowledgeVersion(
            doc_id=doc.id,
            version=doc.version,
            title=doc.title,
            content=doc.content,
            tags=doc.tags,
            attachments=doc.attachments,
            summary=doc.summary,
            publisher_id=user_id,
            publisher_name=user_name,
            change_summary=change_summary,
            publish_time=datetime.now()
        )
        db.session.add(version)
        db.session.commit()
        return version

    # ==================== 浏览埋点 ====================

    @staticmethod
    def record_view(doc_id):
        """记录浏览（增加查看次数）"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        doc.view_count = (doc.view_count or 0) + 1
        db.session.commit()

        return Response.success({'view_count': doc.view_count})

    # ==================== 点赞 ====================

    @staticmethod
    def toggle_like(doc_id, user_id, user_name=None):
        """切换点赞状态"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        existing = KnowledgeLike.query.filter_by(
            doc_id=doc_id,
            user_id=user_id,
            status=1
        ).first()

        if existing:
            existing.delete()
            doc.like_count = max(0, (doc.like_count or 0) - 1)
            liked = False
        else:
            like = KnowledgeLike(
                doc_id=doc_id,
                user_id=user_id,
                user_name=user_name
            )
            db.session.add(like)
            doc.like_count = (doc.like_count or 0) + 1
            liked = True

        db.session.commit()

        return Response.success({
            'liked': liked,
            'like_count': doc.like_count
        })

    # ==================== 评论 ====================

    @staticmethod
    def get_comments(doc_id, page=1, size=20):
        """获取评论列表"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        result = KnowledgeComment.get_by_doc(doc_id, page, size)
        return Response.paginate(
            result['items'],
            result['total'],
            result['page'],
            result['size']
        )

    @staticmethod
    def create_comment(doc_id, data, user_id=None, user_name=None):
        """创建评论"""
        doc = KnowledgeDocument.get_by_id(doc_id)
        if not doc:
            return Response.not_found('文档不存在')

        validation = Validator.validate_form(data, {
            'content': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        parent_id = data.get('parent_id', 0)
        reply_to_id = data.get('reply_to_id')
        reply_to_name = data.get('reply_to_name')

        if parent_id:
            parent = KnowledgeComment.get_by_id(parent_id)
            if not parent or parent.doc_id != doc_id:
                return Response.bad_request('父评论不存在')

        comment = KnowledgeComment(
            doc_id=doc_id,
            parent_id=parent_id,
            content=data['content'],
            commenter_id=user_id,
            commenter_name=user_name,
            reply_to_id=reply_to_id,
            reply_to_name=reply_to_name
        )
        db.session.add(comment)
        db.session.commit()

        return Response.created(comment.to_dict())

    @staticmethod
    def delete_comment(comment_id, user_id=None):
        """删除评论"""
        comment = KnowledgeComment.get_by_id(comment_id)
        if not comment:
            return Response.not_found('评论不存在')

        if user_id and comment.commenter_id and comment.commenter_id != user_id:
            return Response.forbidden('只能删除自己的评论')

        comment.delete()
        return Response.success(message='删除成功')

    # ==================== 全文搜索 ====================

    @staticmethod
    def search_documents(keyword, category_id=None, page=1, size=10):
        """全文搜索文档"""
        result = KnowledgeDocument.search(keyword, category_id, page, size)
        return Response.paginate(
            result['items'],
            result['total'],
            result['page'],
            result['size']
        )
