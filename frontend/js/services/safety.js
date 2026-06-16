/**
 * 安全管理服务
 */
const SafetyService = {
    async getHazardTypes(params = {}) {
        return await Request.get('/safety/hazard-types', params);
    },

    async createHazardType(data) {
        return await Request.post('/safety/hazard-types', data);
    },

    async updateHazardType(typeId, data) {
        return await Request.put(`/safety/hazard-types/${typeId}`, data);
    },

    async deleteHazardType(typeId) {
        return await Request.delete(`/safety/hazard-types/${typeId}`);
    },

    async getInspectionTasks(params = {}) {
        return await Request.get('/safety/inspection-tasks', params);
    },

    async createInspectionTask(data) {
        return await Request.post('/safety/inspection-tasks', data);
    },

    async updateInspectionTask(taskId, data) {
        return await Request.put(`/safety/inspection-tasks/${taskId}`, data);
    },

    async deleteInspectionTask(taskId) {
        return await Request.delete(`/safety/inspection-tasks/${taskId}`);
    },

    async getHazardRecords(params = {}) {
        return await Request.get('/safety/hazard-records', params);
    },

    async getHazardRecord(recordId) {
        return await Request.get(`/safety/hazard-records/${recordId}`);
    },

    async createHazardRecord(data) {
        return await Request.post('/safety/hazard-records', data);
    },

    async updateHazardRecord(recordId, data) {
        return await Request.put(`/safety/hazard-records/${recordId}`, data);
    },

    async deleteHazardRecord(recordId) {
        return await Request.delete(`/safety/hazard-records/${recordId}`);
    },

    async acceptHazard(recordId) {
        return await Request.post(`/safety/hazard-records/${recordId}/accept`, {});
    },

    async getRectificationRecords(params = {}) {
        return await Request.get('/safety/rectification-records', params);
    },

    async createRectificationRecord(data) {
        return await Request.post('/safety/rectification-records', data);
    },

    async updateRectificationRecord(rectId, data) {
        return await Request.put(`/safety/rectification-records/${rectId}`, data);
    },

    async getAccidentRecords(params = {}) {
        return await Request.get('/safety/accident-records', params);
    },

    async getAccidentRecord(recordId) {
        return await Request.get(`/safety/accident-records/${recordId}`);
    },

    async createAccidentRecord(data) {
        return await Request.post('/safety/accident-records', data);
    },

    async updateAccidentRecord(recordId, data) {
        return await Request.put(`/safety/accident-records/${recordId}`, data);
    },

    async deleteAccidentRecord(recordId) {
        return await Request.delete(`/safety/accident-records/${recordId}`);
    },

    async checkOverdue() {
        return await Request.post('/safety/check-overdue', {});
    },

    async getMonthlyReport(params = {}) {
        return await Request.get('/safety/monthly-report', params);
    }
};

window.SafetyService = SafetyService;
