/**
 * 数据模拟服务
 */
const SimulationService = {
    // 获取默认模拟配置
    async getDefaultConfig() {
        return await Request.get('/simulation/config/default');
    },

    // 生成模拟数据
    async generateSimulationData(config = null) {
        const data = config ? { config } : {};
        return await Request.post('/simulation/generate', data);
    },

    // 清除模拟数据
    async clearSimulationData() {
        return await Request.post('/simulation/clear');
    },

    // 获取当前模拟数据状态
    async getSimulationStatus() {
        return await Request.get('/simulation/status');
    },

    // 导入CSV文件
    async importCSV(file, dataType) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', dataType);
        
        return await Request.upload('/simulation/import/csv', formData);
    },

    // 导入JSON文件
    async importJSON(file, dataType) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', dataType);
        
        return await Request.upload('/simulation/import/json', formData);
    },

    // 验证数据
    async validateData(dataType, data) {
        return await Request.post('/simulation/validate', {
            type: dataType,
            data: data
        });
    },

    // 创建模拟数据源
    async createMockDataSource(sourceType, config = {}) {
        return await Request.post('/simulation/source/create', {
            type: sourceType,
            config: config
        });
    },

    // 从数据源生成数据
    async generateFromSource(sourceId, count = 10) {
        return await Request.post(`/simulation/source/${sourceId}/generate`, {
            count: count
        });
    }
};

// 全局可用
window.SimulationService = SimulationService;