/**
 * SOP标准作业管理服务
 */
const SOPService = {
    // SOP文档
    async getSOPs(params = {}) {
        return await Request.get('/api/sop/documents', params);
    },

    async getSOP(sopId) {
        return await Request.get(`/api/sop/documents/${sopId}`);
    },

    async createSOP(data) {
        return await Request.post('/api/sop/documents', data);
    },

    async updateSOP(sopId, data) {
        return await Request.put(`/api/sop/documents/${sopId}`, data);
    },

    async deleteSOP(sopId) {
        return await Request.delete(`/api/sop/documents/${sopId}`);
    },

    async publishSOP(sopId, data) {
        return await Request.post(`/api/sop/documents/${sopId}/publish`, data);
    },

    async getVersionDiff(sopId, params = {}) {
        return await Request.get(`/api/sop/documents/${sopId}/diff`, params);
    },

    // 培训关联
    async addTrainingRelation(sopId, courseId) {
        return await Request.post(`/api/sop/documents/${sopId}/training-relations`, { course_id: courseId });
    },

    async removeTrainingRelation(relationId) {
        return await Request.delete(`/api/sop/training-relations/${relationId}`);
    },

    // 按设备/产品查询
    async getSOPsByEquipment(equipmentId) {
        return await Request.get(`/api/sop/by-equipment/${equipmentId}`);
    },

    async getSOPsByProduct(productName) {
        return await Request.get('/api/sop/by-product', { name: productName });
    },

    // 执行检查表
    async getChecklists(params = {}) {
        return await Request.get('/api/sop/checklists', params);
    },

    async getChecklist(checklistId) {
        return await Request.get(`/api/sop/checklists/${checklistId}`);
    },

    async createChecklist(data) {
        return await Request.post('/api/sop/checklists', data);
    },

    async updateChecklistItem(checklistId, itemId, data) {
        return await Request.put(`/api/sop/checklists/${checklistId}/items/${itemId}`, data);
    },

    async submitChecklist(checklistId, data) {
        return await Request.post(`/api/sop/checklists/${checklistId}/submit`, data);
    },

    async deleteChecklist(checklistId) {
        return await Request.delete(`/api/sop/checklists/${checklistId}`);
    },

    // 合规率统计
    async getComplianceStats(params = {}) {
        return await Request.get('/api/sop/stats/compliance', params);
    }
};

window.SOPService = SOPService;
