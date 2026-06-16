/**
 * 环境监测服务
 */
const EnvMonitorService = {
    baseUrl: '/api/env-monitor',

    // ==================== 区域管理 ====================

    async getAreaTree() {
        return await request.get(`${this.baseUrl}/areas/tree`);
    },

    async getAreas(params = {}) {
        return await request.get(`${this.baseUrl}/areas`, params);
    },

    async getArea(id) {
        return await request.get(`${this.baseUrl}/areas/${id}`);
    },

    async createArea(data) {
        return await request.post(`${this.baseUrl}/areas`, data);
    },

    async updateArea(id, data) {
        return await request.put(`${this.baseUrl}/areas/${id}`, data);
    },

    async deleteArea(id) {
        return await request.delete(`${this.baseUrl}/areas/${id}`);
    },

    // ==================== 监测点管理 ====================

    async getMonitorPoints(params = {}) {
        return await request.get(`${this.baseUrl}/points`, params);
    },

    async getMonitorPoint(id) {
        return await request.get(`${this.baseUrl}/points/${id}`);
    },

    async createMonitorPoint(data) {
        return await request.post(`${this.baseUrl}/points`, data);
    },

    async updateMonitorPoint(id, data) {
        return await request.put(`${this.baseUrl}/points/${id}`, data);
    },

    async deleteMonitorPoint(id) {
        return await request.delete(`${this.baseUrl}/points/${id}`);
    },

    // ==================== 读数管理 ====================

    async addReading(data) {
        return await request.post(`${this.baseUrl}/readings`, data);
    },

    async batchAddReadings(data) {
        return await request.post(`${this.baseUrl}/readings/batch`, data);
    },

    async getRealtimeReadings(params = {}) {
        return await request.get(`${this.baseUrl}/readings/realtime`, params);
    },

    async getHistoryTrend(params) {
        return await request.get(`${this.baseUrl}/readings/history`, params);
    },

    // ==================== 环境标准管理 ====================

    async getStandards(params = {}) {
        return await request.get(`${this.baseUrl}/standards`, params);
    },

    async getAllStandards() {
        return await request.get(`${this.baseUrl}/standards/all`);
    },

    async getStandard(id) {
        return await request.get(`${this.baseUrl}/standards/${id}`);
    },

    async createStandard(data) {
        return await request.post(`${this.baseUrl}/standards`, data);
    },

    async updateStandard(id, data) {
        return await request.put(`${this.baseUrl}/standards/${id}`, data);
    },

    async deleteStandard(id) {
        return await request.delete(`${this.baseUrl}/standards/${id}`);
    },

    // ==================== 数据模拟 ====================

    async generateSimulatedReadings(data) {
        return await request.post(`${this.baseUrl}/simulate`, data);
    },

    async getStatistics() {
        return await request.get(`${this.baseUrl}/statistics`);
    }
};

window.EnvMonitorService = EnvMonitorService;
