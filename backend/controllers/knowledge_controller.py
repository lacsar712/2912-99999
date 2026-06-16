"""
知识库控制器
"""
from flask import Blueprint, request, g
from services.knowledge_service import KnowledgeService
from middleware.auth_middleware import login_required

knowledge_bp = Blueprint('knowledge', __name__)


# ==================== 分类管理 ====================

@knowledge_bp.route('/categories/tree', methods=['GET'])
@login_required
def get_category_tree():
    """获取分类树"""
    return KnowledgeService.get_category_tree()


@knowledge_bp.route('/categories/<int:category_id>', methods=['GET'])
@login_required
def get_category(category_id):
    """获取分类详情"""
    return KnowledgeService.get_category(category_id)


@knowledge_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    """创建分类"""
    data = request.get_json()
    return KnowledgeService.create_category(data)


@knowledge_bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """更新分类"""
    data = request.get_json()
    return KnowledgeService.update_category(category_id, data)


@knowledge_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """删除分类"""
    return KnowledgeService.delete_category(category_id)


# ==================== 文档管理 ====================

@knowledge_bp.route('/documents', methods=['GET'])
@login_required
def get_documents():
    """获取文档列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status')
    keyword = request.args.get('keyword')
    return KnowledgeService.get_documents(category_id, page, size, status, keyword)


@knowledge_bp.route('/documents/<int:doc_id>', methods=['GET'])
@login_required
def get_document(doc_id):
    """获取文档详情"""
    user_id = getattr(g, 'user_id', None)
    return KnowledgeService.get_document(doc_id, user_id)


@knowledge_bp.route('/documents', methods=['POST'])
@login_required
def create_document():
    """创建文档"""
    data = request.get_json()
    user_id = getattr(g, 'user_id', None)
    username = getattr(g, 'username', None)
    return KnowledgeService.create_document(data, user_id, username)


@knowledge_bp.route('/documents/<int:doc_id>', methods=['PUT'])
@login_required
def update_document(doc_id):
    """更新文档"""
    data = request.get_json()
    user_id = getattr(g, 'user_id', None)
    username = getattr(g, 'username', None)
    return KnowledgeService.update_document(doc_id, data, user_id, username)


@knowledge_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    """删除文档"""
    return KnowledgeService.delete_document(doc_id)


# ==================== 发布与版本管理 ====================

@knowledge_bp.route('/documents/<int:doc_id>/publish', methods=['POST'])
@login_required
def publish_document(doc_id):
    """发布文档"""
    data = request.get_json() or {}
    user_id = getattr(g, 'user_id', None)
    username = getattr(g, 'username', None)
    return KnowledgeService.publish_document(doc_id, data, user_id, username)


@knowledge_bp.route('/documents/<int:doc_id>/versions', methods=['GET'])
@login_required
def get_version_history(doc_id):
    """获取版本历史"""
    return KnowledgeService.get_version_history(doc_id)


@knowledge_bp.route('/documents/<int:doc_id>/versions/<int:version_id>/rollback', methods=['POST'])
@login_required
def rollback_version(doc_id, version_id):
    """版本回滚"""
    user_id = getattr(g, 'user_id', None)
    username = getattr(g, 'username', None)
    return KnowledgeService.rollback_version(doc_id, version_id, user_id, username)


# ==================== 浏览埋点 ====================

@knowledge_bp.route('/documents/<int:doc_id>/view', methods=['POST'])
@login_required
def record_view(doc_id):
    """记录浏览"""
    return KnowledgeService.record_view(doc_id)


# ==================== 点赞 ====================

@knowledge_bp.route('/documents/<int:doc_id>/like', methods=['POST'])
@login_required
def toggle_like(doc_id):
    """切换点赞"""
    user_id = getattr(g, 'user_id', None)
    username = getattr(g, 'username', None)
    return KnowledgeService.toggle_like(doc_id, user_id, username)


# ==================== 评论 ====================

@knowledge_bp.route('/documents/<int:doc_id>/comments', methods=['GET'])
@login_required
def get_comments(doc_id):
    """获取评论列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    return KnowledgeService.get_comments(doc_id, page, size)


@knowledge_bp.route('/documents/<int:doc_id>/comments', methods=['POST'])
@login_required
def create_comment(doc_id):
    """创建评论"""
    data = request.get_json()
    user_id = getattr(g, 'user_id', None)
    username = getattr(g, 'username', None)
    return KnowledgeService.create_comment(doc_id, data, user_id, username)


@knowledge_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """删除评论"""
    user_id = getattr(g, 'user_id', None)
    return KnowledgeService.delete_comment(comment_id, user_id)


# ==================== 全文搜索 ====================

@knowledge_bp.route('/search', methods=['GET'])
@login_required
def search_documents():
    """全文搜索"""
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    return KnowledgeService.search_documents(keyword, category_id, page, size)
