/**
 * 不合格品处置服务
 */
const DisposalService = {
    async getOrders(params = {}) {
        return await Request.get('/disposal/orders', params);
    },

    async getMyPendingApprovals(params = {}) {
        return await Request.get('/disposal/orders/pending-approval', params);
    },

    async getOrderById(id) {
        return await Request.get(`/disposal/orders/${id}`);
    },

    async createOrder(data) {
        return await Request.post('/disposal/orders', data);
    },

    async quickCreateFromQuality(recordId, data) {
        return await Request.post(`/disposal/orders/quick-create/${recordId}`, data);
    },

    async updateOrder(id, data) {
        return await Request.put(`/disposal/orders/${id}`, data);
    },

    async deleteOrder(id) {
        return await Request.delete(`/disposal/orders/${id}`);
    },

    async submitOrder(id) {
        return await Request.post(`/disposal/orders/${id}/submit`);
    },

    async approveOrder(id, data = {}) {
        return await Request.post(`/disposal/orders/${id}/approve`, data);
    },

    async rejectOrder(id, data = {}) {
        return await Request.post(`/disposal/orders/${id}/reject`, data);
    },

    async returnOrder(id, data = {}) {
        return await Request.post(`/disposal/orders/${id}/return`, data);
    },

    async recordResult(id, data) {
        return await Request.post(`/disposal/orders/${id}/result`, data);
    },

    async getMonthlyStatistics(params = {}) {
        return await Request.get('/disposal/statistics/monthly', params);
    },

    async getTrendStatistics(params = {}) {
        return await Request.get('/disposal/statistics/trend', params);
    },

    async getDashboard() {
        return await Request.get('/disposal/statistics/dashboard');
    }
};

window.DisposalService = DisposalService;
