/**
 * 设备模拟数据服务
 * 用于设备管理页面的数据模拟功能
 */
const EquipmentSimulationService = {
    /**
     * 获取设备模拟配置
     */
    async getSimulationConfig() {
        return await Request.get('/simulation/equipment/config');
    },

    /**
     * 获取设备模拟数据
     * @param {Object} params - 查询参数
     * @param {number} params.page - 页码
     * @param {number} params.size - 每页大小
     * @param {number} params.lineId - 生产线ID筛选
     * @param {string} params.status - 设备状态筛选
     * @param {string[]} params.sourceIds - 数据源ID列表
     * @param {boolean} params.useRealData - 是否使用真实数据
     */
    async getSimulationData(params = {}) {
        return await Request.get('/simulation/equipment/data', params);
    },

    /**
     * 创建设备模拟数据源
     * @param {string} type - 数据源类型 (api, websocket, file_stream, user_input)
     * @param {Object} config - 数据源配置
     */
    async createDataSource(type, config = {}) {
        return await Request.post('/simulation/equipment/source/create', {
            type,
            config
        });
    },

    /**
     * 启动设备数据自动刷新
     * @param {number} interval - 刷新间隔（秒）
     * @param {string} callbackUrl - 回调URL（可选）
     */
    async startAutoRefresh(interval = 30, callbackUrl = null) {
        const data = { interval };
        if (callbackUrl) {
            data.callbackUrl = callbackUrl;
        }
        return await Request.post('/simulation/equipment/refresh/start', data);
    },

    /**
     * 停止设备数据自动刷新
     */
    async stopAutoRefresh() {
        return await Request.post('/simulation/equipment/refresh/stop');
    },

    /**
     * 列出可用的设备数据源
     */
    async listDataSources() {
        return await Request.get('/simulation/equipment/sources');
    },

    /**
     * 获取当前数据源状态
     */
    async getDataSourceStatus(sourceId) {
        // 注意：这里需要调用数据源管理器的API
        // 暂时使用通用API，后续可以扩展
        return await Request.get(`/simulation/source/${sourceId}/status`);
    },

    /**
     * 从数据源生成设备数据
     * @param {string} sourceId - 数据源ID
     * @param {number} count - 生成数据条数
     */
    async generateFromSource(sourceId, count = 10) {
        return await Request.post(`/simulation/source/${sourceId}/generate`, { count });
    },

    /**
     * 创建默认的API数据源
     */
    async createDefaultAPIDataSource() {
        return this.createDataSource('api', {
            endpoint: '/api/simulation/equipment',
            method: 'GET',
            interval: 5,
            batch_size: 10
        });
    },

    /**
     * 创建默认的WebSocket数据源
     */
    async createDefaultWebSocketDataSource() {
        return this.createDataSource('websocket', {
            url: 'ws://localhost:5001/ws/equipment',
            interval: 1,
            real_time: true
        });
    },

    /**
     * 创建默认的文件流数据源
     */
    async createDefaultFileStreamDataSource() {
        return this.createDataSource('file_stream', {
            file_path: '/data/equipment_stream.csv',
            format: 'csv',
            interval: 10
        });
    },

    /**
     * 创建默认的用户输入数据源
     */
    async createDefaultUserInputDataSource() {
        return this.createDataSource('user_input', {
            form_config: {
                fields: [
                    { name: 'equipment_name', type: 'text', label: '设备名称', required: true },
                    { name: 'status', type: 'select', label: '状态', 
                      options: ['running', 'idle', 'maintenance', 'error', 'offline'] },
                    { name: 'temperature', type: 'number', label: '温度(℃)' },
                    { name: 'pressure', type: 'number', label: '压力(MPa)' }
                ]
            }
        });
    },

    /**
     * 切换数据模式（真实数据/模拟数据）
     * @param {boolean} useSimulation - 是否使用模拟数据
     * @param {string[]} sourceIds - 数据源ID列表（仅模拟数据有效）
     */
    async switchDataMode(useSimulation = false, sourceIds = []) {
        // 保存用户偏好到本地存储
        Storage.set('equipment_data_mode', useSimulation ? 'simulation' : 'real');
        if (sourceIds.length > 0) {
            Storage.set('equipment_data_sources', JSON.stringify(sourceIds));
        }
        
        return {
            success: true,
            mode: useSimulation ? 'simulation' : 'real',
            sourceIds: sourceIds
        };
    },

    /**
     * 获取当前数据模式
     */
    getCurrentDataMode() {
        return Storage.get('equipment_data_mode') || 'real';
    },

    /**
     * 获取保存的数据源
     */
    getSavedDataSources() {
        const sources = Storage.get('equipment_data_sources');
        return sources ? JSON.parse(sources) : [];
    },

    /**
     * 初始化模拟数据环境
     */
    async initializeSimulationEnvironment() {
        try {
            // 1. 检查模拟配置
            const configRes = await this.getSimulationConfig();
            if (configRes.code !== 200) {
                console.warn('获取模拟配置失败:', configRes.message);
            }

            // 2. 检查是否有保存的数据源偏好
            const savedSources = this.getSavedDataSources();
            if (savedSources.length > 0) {
                console.log('使用保存的数据源:', savedSources);
            }

            // 3. 如果没有数据源，创建默认数据源
            const sourcesRes = await this.listDataSources();
            if (sourcesRes.code === 200 && sourcesRes.data.count === 0) {
                console.log('创建默认数据源...');
                await this.createDefaultAPIDataSource();
                await this.createDefaultWebSocketDataSource();
            }

            return {
                success: true,
                message: '模拟环境初始化完成'
            };
        } catch (error) {
            console.error('初始化模拟环境失败:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
};

// 导出服务
window.EquipmentSimulationService = EquipmentSimulationService;