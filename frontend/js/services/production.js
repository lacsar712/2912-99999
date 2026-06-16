/**
 * 生产线监控服务
 */
const ProductionService = {
    // 生产线
    async getLines(params = {}) {
        return await Request.get('/production/lines', params);
    },

    async getLineById(id) {
        return await Request.get(`/production/lines/${id}`);
    },

    async createLine(data) {
        return await Request.post('/production/lines', data);
    },

    async updateLine(id, data) {
        return await Request.put(`/production/lines/${id}`, data);
    },

    async deleteLine(id) {
        return await Request.delete(`/production/lines/${id}`);
    },

    // 设备
    async getEquipments(params = {}) {
        return await Request.get('/production/equipments', params);
    },

    async getEquipmentById(id) {
        return await Request.get(`/production/equipments/${id}`);
    },

    async createEquipment(data) {
        return await Request.post('/production/equipments', data);
    },

    async updateEquipment(id, data) {
        return await Request.put(`/production/equipments/${id}`, data);
    },

    async controlEquipment(id, action) {
        return await Request.post(`/production/equipments/${id}/control`, { action });
    },

    // 传感器
    async getSensors(params = {}) {
        return await Request.get('/production/sensors', params);
    },

    async getSensorRealtime(params = {}) {
        return await Request.get('/production/sensors/realtime', params);
    },

    // 任务
    async getTasks(params = {}) {
        return await Request.get('/production/tasks', params);
    },

    async createTask(data) {
        return await Request.post('/production/tasks', data);
    },

    async updateTaskStatus(id, status) {
        return await Request.put(`/production/tasks/${id}/status`, { status });
    },

    // 统计
    async getDashboard() {
        return await Request.get('/production/dashboard');
    },

    async getTrend(days = 7) {
        return await Request.get('/production/trend', { days });
    }
};

// 全局可用
window.ProductionService = ProductionService;
