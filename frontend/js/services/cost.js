/**
 * 成本核算服务
 */
const CostService = {
    async getElements(params = {}) {
        return await Request.get('/cost/elements', params);
    },

    async getAllElements() {
        return await Request.get('/cost/elements/all');
    },

    async getElementById(id) {
        return await Request.get(`/cost/elements/${id}`);
    },

    async createElement(data) {
        return await Request.post('/cost/elements', data);
    },

    async updateElement(id, data) {
        return await Request.put(`/cost/elements/${id}`, data);
    },

    async deleteElement(id) {
        return await Request.delete(`/cost/elements/${id}`);
    },

    async getRecords(params = {}) {
        return await Request.get('/cost/records', params);
    },

    async getRecordById(id) {
        return await Request.get(`/cost/records/${id}`);
    },

    async createRecord(data) {
        return await Request.post('/cost/records', data);
    },

    async batchCreateRecords(data) {
        return await Request.post('/cost/records/batch', data);
    },

    async updateRecord(id, data) {
        return await Request.put(`/cost/records/${id}`, data);
    },

    async deleteRecord(id) {
        return await Request.delete(`/cost/records/${id}`);
    },

    async calculateTaskCost(taskId) {
        return await Request.post(`/cost/tasks/${taskId}/calculate-cost`);
    },

    async getTaskCost(taskId) {
        return await Request.get(`/cost/tasks/${taskId}/cost`);
    },

    async getMultiDimensionReport(params = {}) {
        return await Request.get('/cost/report/multi-dimension', params);
    },

    async getMonthlySummary(months = 12) {
        return await Request.get('/cost/report/monthly-summary', { months });
    },

    async getDashboardCost() {
        return await Request.get('/cost/report/dashboard-cost');
    },

    async exportCSV(params = {}) {
        return await Request.get('/cost/report/export-csv', params);
    }
};

window.CostService = CostService;
