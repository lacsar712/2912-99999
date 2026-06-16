/**
 * 维修工单服务
 */
const MaintenanceService = {
    async getWorkOrders(params = {}) {
        return await Request.get('/maintenance/work-orders', params);
    },

    async getWorkOrderById(id) {
        return await Request.get(`/maintenance/work-orders/${id}`);
    },

    async createWorkOrder(data) {
        return await Request.post('/maintenance/work-orders', data);
    },

    async updateWorkOrder(id, data) {
        return await Request.put(`/maintenance/work-orders/${id}`, data);
    },

    async updateWorkOrderStatus(id, status) {
        return await Request.put(`/maintenance/work-orders/${id}/status`, { status });
    },

    async deleteWorkOrder(id) {
        return await Request.delete(`/maintenance/work-orders/${id}`);
    },

    async getStatistics() {
        return await Request.get('/maintenance/work-orders/statistics');
    }
};

window.MaintenanceService = MaintenanceService;
