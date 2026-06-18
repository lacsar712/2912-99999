/**
 * 系统健康状态服务
 */
const HealthService = {
    async getFullHealth() {
        try {
            return await Request.get('/health');
        } catch (e) {
            return { code: 503, status: 'unhealthy', components: {}, message: '无法连接到后端服务' };
        }
    },

    async getComponents() {
        try {
            return await Request.get('/health/components');
        } catch (e) {
            return { code: 503, data: { components: {}, degradation: {} } };
        }
    },

    async getHealLog() {
        try {
            return await Request.get('/health/heal-log');
        } catch (e) {
            return { code: 503, data: { records: [], total: 0 } };
        }
    }
};

window.HealthService = HealthService;
