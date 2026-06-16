/**
 * 统计服务
 */
const StatisticsService = {
    /**
     * 获取统计概览
     * @returns {Promise}
     */
    async getOverview() {
        return await Request.get('/statistics/overview');
    },

    /**
     * 获取类型统计
     * @returns {Promise}
     */
    async getTypeStatistics() {
        return await Request.get('/statistics/type');
    },

    /**
     * 获取用户统计
     * @returns {Promise}
     */
    async getUserStatistics() {
        return await Request.get('/statistics/user');
    },

    /**
     * 获取操作日志
     * @param {Object} params - 查询参数
     * @returns {Promise}
     */
    async getOperationLog(params = {}) {
        return await Request.get('/statistics/log', params);
    }
};

// 全局可用
window.StatisticsService = StatisticsService;
