/**
 * 告警服务
 */
const AlertService = {
    /**
     * 获取告警列表
     * @param {Object} params - 查询参数
     * @returns {Promise}
     */
    async getAlerts(params = {}) {
        return await Request.get('/alerts/list', params);
    },

    /**
     * 获取告警详情
     * @param {number} alertId - 告警ID
     * @returns {Promise}
     */
    async getAlert(alertId) {
        return await Request.get(`/alerts/${alertId}`);
    },

    /**
     * 创建告警
     * @param {Object} data - 告警数据
     * @returns {Promise}
     */
    async createAlert(data) {
        return await Request.post('/alerts/', data);
    },

    /**
     * 确认告警
     * @param {number} alertId - 告警ID
     * @param {string} note - 备注
     * @returns {Promise}
     */
    async acknowledgeAlert(alertId, note = null) {
        return await Request.post(`/alerts/${alertId}/acknowledge`, { note });
    },

    /**
     * 解决告警
     * @param {number} alertId - 告警ID
     * @param {string} note - 备注
     * @returns {Promise}
     */
    async resolveAlert(alertId, note = null) {
        return await Request.post(`/alerts/${alertId}/resolve`, { note });
    },

    /**
     * 批量解决告警
     * @param {Array} alertIds - 告警ID列表
     * @param {string} note - 备注
     * @returns {Promise}
     */
    async batchResolve(alertIds, note = null) {
        return await Request.post('/alerts/batch-resolve', { alert_ids: alertIds, note });
    },

    /**
     * 获取告警统计
     * @returns {Promise}
     */
    async getStatistics() {
        return await Request.get('/alerts/statistics');
    }
};

// 全局可用
window.AlertService = AlertService;
