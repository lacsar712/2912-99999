/**
 * 知识库服务模块
 */
const KnowledgeService = {
    baseURL: '/api/knowledge',

    // ==================== 分类管理 ====================

    async getCategoryTree() {
        const result = await Request.get(this.baseURL + '/categories/tree');
        return result;
    },

    async getCategory(categoryId) {
        const result = await Request.get(this.baseURL + '/categories/' + categoryId);
        return result;
    },

    async createCategory(data) {
        const result = await Request.post(this.baseURL + '/categories', data);
        return result;
    },

    async updateCategory(categoryId, data) {
        const result = await Request.put(this.baseURL + '/categories/' + categoryId, data);
        return result;
    },

    async deleteCategory(categoryId) {
        const result = await Request.delete(this.baseURL + '/categories/' + categoryId);
        return result;
    },

    // ==================== 文档管理 ====================

    async getDocuments(params) {
        const result = await Request.get(this.baseURL + '/documents', params);
        return result;
    },

    async getDocument(docId) {
        const result = await Request.get(this.baseURL + '/documents/' + docId);
        return result;
    },

    async createDocument(data) {
        const result = await Request.post(this.baseURL + '/documents', data);
        return result;
    },

    async updateDocument(docId, data) {
        const result = await Request.put(this.baseURL + '/documents/' + docId, data);
        return result;
    },

    async deleteDocument(docId) {
        const result = await Request.delete(this.baseURL + '/documents/' + docId);
        return result;
    },

    // ==================== 发布与版本管理 ====================

    async publishDocument(docId, data) {
        const result = await Request.post(this.baseURL + '/documents/' + docId + '/publish', data);
        return result;
    },

    async getVersionHistory(docId) {
        const result = await Request.get(this.baseURL + '/documents/' + docId + '/versions');
        return result;
    },

    async rollbackVersion(docId, versionId) {
        const result = await Request.post(this.baseURL + '/documents/' + docId + '/versions/' + versionId + '/rollback');
        return result;
    },

    // ==================== 浏览埋点 ====================

    async recordView(docId) {
        const result = await Request.post(this.baseURL + '/documents/' + docId + '/view');
        return result;
    },

    // ==================== 点赞 ====================

    async toggleLike(docId) {
        const result = await Request.post(this.baseURL + '/documents/' + docId + '/like');
        return result;
    },

    // ==================== 评论 ====================

    async getComments(docId, params) {
        const result = await Request.get(this.baseURL + '/documents/' + docId + '/comments', params);
        return result;
    },

    async createComment(docId, data) {
        const result = await Request.post(this.baseURL + '/documents/' + docId + '/comments', data);
        return result;
    },

    async deleteComment(commentId) {
        const result = await Request.delete(this.baseURL + '/comments/' + commentId);
        return result;
    },

    // ==================== 全文搜索 ====================

    async searchDocuments(params) {
        const result = await Request.get(this.baseURL + '/search', params);
        return result;
    }
};

window.KnowledgeService = KnowledgeService;
