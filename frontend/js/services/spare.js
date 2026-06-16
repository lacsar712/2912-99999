/**
 * 备件库存服务
 */
const SpareService = {
    async getEquipmentTypes() {
        return await Request.get('/spare/parts/equipment-types');
    },

    async checkLowStock() {
        return await Request.post('/spare/parts/check-low-stock');
    },

    async getParts(params = {}) {
        return await Request.get('/spare/parts', params);
    },

    async getPartById(id) {
        return await Request.get(`/spare/parts/${id}`);
    },

    async createPart(data) {
        return await Request.post('/spare/parts', data);
    },

    async updatePart(id, data) {
        return await Request.put(`/spare/parts/${id}`, data);
    },

    async deletePart(id) {
        return await Request.delete(`/spare/parts/${id}`);
    },

    async getInbounds(params = {}) {
        return await Request.get('/spare/inbounds', params);
    },

    async createInbound(data) {
        return await Request.post('/spare/inbounds', data);
    },

    async deleteInbound(id) {
        return await Request.delete(`/spare/inbounds/${id}`);
    },

    async getOutbounds(params = {}) {
        return await Request.get('/spare/outbounds', params);
    },

    async createOutbound(data) {
        return await Request.post('/spare/outbounds', data);
    },

    async returnOutbound(id) {
        return await Request.post(`/spare/outbounds/${id}/return`);
    },

    async deleteOutbound(id) {
        return await Request.delete(`/spare/outbounds/${id}`);
    },

    async getInventories(params = {}) {
        return await Request.get('/spare/inventories', params);
    },

    async createInventory(data) {
        return await Request.post('/spare/inventories', data);
    },

    async batchCreateInventory(data) {
        return await Request.post('/spare/inventories/batch', data);
    },

    async updateInventory(id, data) {
        return await Request.put(`/spare/inventories/${id}`, data);
    },

    async deleteInventory(id) {
        return await Request.delete(`/spare/inventories/${id}`);
    },

    async getTurnoverRate(params = {}) {
        return await Request.get('/spare/statistics/turnover', params);
    },

    async getDashboard() {
        return await Request.get('/spare/statistics/dashboard');
    }
};

window.SpareService = SpareService;
