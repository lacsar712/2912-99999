/**
 * 数据模拟页面 - 支持多数据源
 */
const SimulationPage = {
    currentConfig: null,
    chartInstances: {},
    dataTable: null,
    currentData: [],
    dataSources: [],  // 存储创建的数据源
    selectedSourceId: null,

    init() {
        this.loadDefaultConfig();
        this.loadSimulationStatus();
        this.loadProductionLines();
        this.loadDataSources();
        this.initEventListeners();
    },

    destroy() {
        // 移除事件监听器
        if (this._handleClick) {
            document.removeEventListener('click', this._handleClick);
        }
        
        Object.values(this.chartInstances).forEach(chart => {
            if (chart.destroy) chart.destroy();
        });
        this.chartInstances = {};
        if (this.dataTable) {
            this.dataTable.destroy?.();
            this.dataTable = null;
        }
    },

    async loadDefaultConfig() {
        try {
            const response = await SimulationService.getDefaultConfig();
            if (response.code === 200) {
                this.currentConfig = response.data;
                this.renderConfigForm();
            }
        } catch (error) {
            console.error('加载默认配置失败:', error);
            this.renderConfigForm();
        }
    },

    async loadSimulationStatus() {
        try {
            const response = await SimulationService.getSimulationStatus();
            if (response.code === 200) {
                this.renderStatus(response.data);
                this.renderCharts(response.data);
            }
        } catch (error) {
            console.error('加载模拟状态失败:', error);
        }
    },

    async loadProductionLines() {
        try {
            const response = await ProductionService.getLines({ size: 100 });
            if (response.code === 200) {
                this.currentData = response.data.items || response.data.list || [];
                this.renderDataTable();
            }
        } catch (error) {
            console.error('加载生产线数据失败:', error);
        }
    },

    async loadDataSources() {
        try {
            const response = await Request.get('/center/sources');
            if (response.code === 200) {
                this.dataSources = response.data.sources || [];
                this.renderDataSources();
            }
        } catch (error) {
            console.error('加载数据源失败:', error);
        }
    },

    renderConfigForm() {
        const container = document.getElementById('pageContainer');
        const configHtml = this.generateConfigHtml();
        
        container.innerHTML = `
            <div class="page-header" style="margin-bottom: 24px;">
                <h2 style="margin: 0;">数据模拟</h2>
                <p class="page-description" style="color: var(--text-secondary); margin-top: 8px;">
                    生成模拟生产线监控数据，支持多种数据源模拟
                </p>
            </div>

            <div class="grid" style="display: grid; grid-template-columns: 350px 1fr; gap: 24px;">
                <!-- 左侧配置面板 -->
                <div class="config-panel">
                    <!-- 模拟配置卡片 -->
                    <div class="card" style="margin-bottom: 16px;">
                        <div class="card-header">
                            <h4 class="card-title">模拟配置</h4>
                        </div>
                        <div class="card-body">
                            <form id="simulationConfigForm">${configHtml}</form>
                        </div>
                        <div class="card-footer" style="padding: 16px;">
                            <button class="btn btn-primary" id="generateBtn" style="width: 100%;">
                                生成模拟数据
                            </button>
                            <button class="btn btn-danger" id="clearBtn" style="width: 100%; margin-top: 8px;">
                                清除模拟数据
                            </button>
                        </div>
                    </div>

                    <!-- 多数据源管理卡片 -->
                    <div class="card">
                        <div class="card-header">
                            <h4 class="card-title">数据源管理</h4>
                        </div>
                        <div class="card-body">
                            <!-- 创建数据源 -->
                            <div style="margin-bottom: 16px;">
                                <label class="form-label">数据源类型</label>
                                <select class="form-control" id="sourceTypeSelect">
                                    <option value="api">API数据源</option>
                                    <option value="websocket">WebSocket数据源</option>
                                    <option value="file_stream">文件流数据源</option>
                                    <option value="user_input">用户输入数据源</option>
                                </select>
                            </div>
                            
                            <!-- API配置 -->
                            <div id="apiConfig" class="source-config">
                                <div style="margin-bottom: 12px;">
                                    <label class="form-label">API端点</label>
                                    <input type="text" class="form-control" id="apiEndpoint" 
                                           value="/api/simulation/generate" placeholder="/api/data">
                                </div>
                                <div style="margin-bottom: 12px;">
                                    <label class="form-label">请求方法</label>
                                    <select class="form-control" id="apiMethod">
                                        <option value="GET">GET</option>
                                        <option value="POST">POST</option>
                                    </select>
                                </div>
                            </div>

                            <!-- WebSocket配置 -->
                            <div id="websocketConfig" class="source-config" style="display: none;">
                                <div style="margin-bottom: 12px;">
                                    <label class="form-label">WebSocket URL</label>
                                    <input type="text" class="form-control" id="wsUrl" 
                                           value="ws://localhost:5001/ws" placeholder="ws://host/ws">
                                </div>
                            </div>

                            <!-- 文件流配置 -->
                            <div id="fileStreamConfig" class="source-config" style="display: none;">
                                <div style="margin-bottom: 12px;">
                                    <label class="form-label">文件格式</label>
                                    <select class="form-control" id="fileFormat">
                                        <option value="csv">CSV</option>
                                        <option value="json">JSON</option>
                                    </select>
                                </div>
                            </div>

                            <!-- 用户输入配置 -->
                            <div id="userInputConfig" class="source-config" style="display: none;">
                                <div style="margin-bottom: 12px;">
                                    <label class="form-label">输入字段</label>
                                    <input type="text" class="form-control" id="inputFields" 
                                           value="value" placeholder="字段名,逗号分隔">
                                </div>
                            </div>

                            <button class="btn btn-info" id="createSourceBtn" style="width: 100%;">
                                创建数据源
                            </button>

                            <!-- 数据源列表 -->
                            <div style="margin-top: 16px;">
                                <label class="form-label">已创建的数据源</label>
                                <div id="dataSourcesList"></div>
                            </div>
                        </div>
                    </div>

                    <!-- 文件导入卡片 -->
                    <div class="card" style="margin-top: 16px;">
                        <div class="card-header">
                            <h4 class="card-title">文件导入</h4>
                        </div>
                        <div class="card-body">
                            <div style="margin-bottom: 12px;">
                                <label class="form-label">数据类型</label>
                                <select class="form-control" id="dataTypeSelect">
                                    <option value="production_line">生产线数据</option>
                                    <option value="equipment">设备数据</option>
                                    <option value="sensor">传感器数据</option>
                                    <option value="record">生产记录数据</option>
                                    <option value="alert">告警记录数据</option>
                                </select>
                            </div>
                            <div style="margin-bottom: 12px;">
                                <input type="file" class="form-control" id="fileInput" accept=".csv,.json">
                            </div>
                            <button class="btn btn-success" id="uploadBtn" style="width: 100%;">
                                导入数据
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 右侧状态面板 -->
                <div class="status-panel">
                    <div class="card">
                        <div class="card-header">
                            <h4 class="card-title">当前数据状态</h4>
                        </div>
                        <div class="card-body">
                            <div id="statusContainer">
                                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                                    加载中...
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 图表区域 -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px;">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title">生产线状态分布</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="lineStatusChart" height="200"></canvas>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title">设备状态分布</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="equipmentStatusChart" height="200"></canvas>
                            </div>
                        </div>
                    </div>

                    <!-- 数据表格 -->
                    <div class="card" style="margin-top: 16px;">
                        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                            <h5 class="card-title" style="margin: 0;">生产线数据</h5>
                            <button class="btn btn-sm btn-outline" id="refreshDataBtn">刷新</button>
                        </div>
                        <div class="card-body">
                            <div id="dataTableContainer"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 绑定数据源类型切换
        this.bindSourceTypeChange();
    },

    bindSourceTypeChange() {
        const sourceTypeSelect = document.getElementById('sourceTypeSelect');
        if (sourceTypeSelect) {
            sourceTypeSelect.addEventListener('change', (e) => {
                // 隐藏所有配置
                document.querySelectorAll('.source-config').forEach(el => {
                    el.style.display = 'none';
                });
                // 显示对应配置
                const type = e.target.value;
                const configId = type === 'api' ? 'apiConfig' : 
                                type === 'websocket' ? 'websocketConfig' :
                                type === 'file_stream' ? 'fileStreamConfig' : 'userInputConfig';
                const configEl = document.getElementById(configId);
                if (configEl) configEl.style.display = 'block';
            });
        }
    },

    renderDataSources() {
        const container = document.getElementById('dataSourcesList');
        if (!container) return;

        if (this.dataSources.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 13px;">
                    暂无数据源，请创建
                </div>
            `;
            return;
        }

        container.innerHTML = this.dataSources.map(source => `
            <div class="source-item" style="
                padding: 12px; 
                border: 1px solid var(--border-color); 
                border-radius: 8px; 
                margin-bottom: 8px;
                cursor: pointer;
                ${this.selectedSourceId === source.id ? 'border-color: var(--primary-color); background: rgba(0,123,255,0.05);' : ''}
            " onclick="SimulationPage.selectSource('${source.id}')">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 500;">${this.getSourceTypeLabel(source.type)}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            ${source.name || source.id}
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <span class="status-badge ${source.status === 'active' ? 'running' : 'stopped'}">
                            ${source.status === 'active' ? '活跃' : '停止'}
                        </span>
                        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); SimulationPage.deleteSource('${source.id}')">
                            删除
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // 添加数据生成按钮
        if (this.selectedSourceId) {
            container.innerHTML += `
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-color);">
                    <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                        <input type="number" class="form-control" id="generateCount" value="10" min="1" max="100" style="width: 80px;">
                        <span style="line-height: 36px; font-size: 13px;">条数据</span>
                    </div>
                    <button class="btn btn-warning" id="generateFromSourceBtn" style="width: 100%;">
                        从数据源生成数据
                    </button>
                </div>
            `;
        }
    },

    getSourceTypeLabel(type) {
        const labels = {
            api: '🔗 API数据源',
            websocket: '🔌 WebSocket数据源',
            file_stream: '📁 文件流数据源',
            user_input: '✏️ 用户输入数据源'
        };
        return labels[type] || type;
    },

    selectSource(sourceId) {
        this.selectedSourceId = sourceId;
        this.renderDataSources();
    },

    async deleteSource(sourceId) {
        if (!confirm('确定要删除此数据源吗？')) return;
        
        try {
            const response = await Request.delete(`/center/sources/${sourceId}`);
            if (response.code === 200) {
                Toast.success('数据源已删除');
                this.dataSources = this.dataSources.filter(s => s.id !== sourceId);
                if (this.selectedSourceId === sourceId) {
                    this.selectedSourceId = null;
                }
                this.renderDataSources();
            } else {
                Toast.error(response.message || '删除失败');
            }
        } catch (error) {
            console.error('删除数据源失败:', error);
            Toast.error('删除失败');
        }
    },

    generateConfigHtml() {
        const config = this.currentConfig || {};
        return `
            <div class="form-group">
                <label>生产线数量</label>
                <input type="number" class="form-control" name="lines.count" 
                       value="${config.lines?.count || 3}" min="1" max="20">
            </div>
            <div class="form-group">
                <label>每条生产线设备数</label>
                <input type="number" class="form-control" name="equipments.per_line" 
                       value="${config.equipments?.per_line || 3}" min="1" max="10">
            </div>
            <div class="form-group">
                <label>每个设备传感器数</label>
                <input type="number" class="form-control" name="sensors.per_equipment" 
                       value="${config.sensors?.per_equipment || 4}" min="1" max="10">
            </div>
            <div class="form-group">
                <label>生产任务数量</label>
                <input type="number" class="form-control" name="tasks.count" 
                       value="${config.tasks?.count || 10}" min="1" max="50">
            </div>
            <div class="form-group">
                <label>生成记录天数</label>
                <input type="number" class="form-control" name="records.days" 
                       value="${config.records?.days || 7}" min="1" max="30">
            </div>
        `;
    },

    renderStatus(data) {
        const container = document.getElementById('statusContainer');
        if (!container) return;

        const counts = data.counts || {};
        const status = data.status_distribution || {};

        const countItems = [
            { label: '生产线', count: counts.production_lines || 0, icon: '🏭', color: 'primary' },
            { label: '设备', count: counts.equipments || 0, icon: '⚙️', color: 'success' },
            { label: '传感器', count: counts.sensors || 0, icon: '📡', color: 'warning' },
            { label: '任务', count: counts.production_tasks || 0, icon: '📋', color: 'info' },
            { label: '记录', count: counts.production_records || 0, icon: '📊', color: 'secondary' },
            { label: '告警', count: counts.alert_records || 0, icon: '🔔', color: 'danger' }
        ];

        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
                ${countItems.map(item => `
                    <div class="stat-card" style="text-align: center; padding: 16px;">
                        <div style="font-size: 24px; margin-bottom: 8px;">${item.icon}</div>
                        <div style="font-size: 24px; font-weight: bold; color: var(--${item.color}-color);">${item.count}</div>
                        <div style="font-size: 13px; color: var(--text-secondary);">${item.label}</div>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top: 20px;">
                <h5 style="margin-bottom: 12px;">状态分布</h5>
                <table class="data-table" style="font-size: 13px;">
                    <thead>
                        <tr>
                            <th>类型</th>
                            <th>运行中</th>
                            <th>停止/空闲</th>
                            <th>维护</th>
                            <th>错误</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>生产线</td>
                            <td>${status.lines?.running || 0}</td>
                            <td>${status.lines?.stopped || 0}</td>
                            <td>${status.lines?.maintenance || 0}</td>
                            <td>${status.lines?.error || 0}</td>
                        </tr>
                        <tr>
                            <td>设备</td>
                            <td>${status.equipments?.running || 0}</td>
                            <td>${status.equipments?.idle || 0}</td>
                            <td>${status.equipments?.maintenance || 0}</td>
                            <td>${status.equipments?.error || 0}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    },

    renderCharts(data) {
        const status = data.status_distribution || {};

        this.renderPieChart('lineStatusChart', '生产线状态', status.lines || {}, [
            { key: 'running', label: '运行中', color: '#28a745' },
            { key: 'stopped', label: '停止', color: '#6c757d' },
            { key: 'maintenance', label: '维护', color: '#ffc107' },
            { key: 'error', label: '错误', color: '#dc3545' }
        ]);

        this.renderPieChart('equipmentStatusChart', '设备状态', status.equipments || {}, [
            { key: 'running', label: '运行中', color: '#28a745' },
            { key: 'idle', label: '空闲', color: '#17a2b8' },
            { key: 'maintenance', label: '维护', color: '#ffc107' },
            { key: 'error', label: '错误', color: '#dc3545' }
        ]);
    },

    renderPieChart(canvasId, title, data, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (this.chartInstances[canvasId]) {
            this.chartInstances[canvasId].destroy();
        }

        const ctx = canvas.getContext('2d');
        const labels = config.map(item => item.label);
        const values = config.map(item => data[item.key] || 0);
        const colors = config.map(item => item.color);

        if (values.every(v => v === 0)) values[0] = 1;

        this.chartInstances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{ data: values, backgroundColor: colors, borderWidth: 2 }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 12, padding: 8 } }
                }
            }
        });
    },

    renderDataTable() {
        const container = document.getElementById('dataTableContainer');
        if (!container) return;

        if (!this.currentData.length) {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">暂无数据</div>';
            return;
        }

        const rows = this.currentData.map(line => `
            <tr>
                <td>${line.line_code || '-'}</td>
                <td>${line.line_name || '-'}</td>
                <td><span class="status-badge ${line.status}">${line.status || '-'}</span></td>
                <td>${line.capacity || '-'}</td>
                <td>${line.location || '-'}</td>
                <td>${line.supervisor || '-'}</td>
            </tr>
        `).join('');

        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>编号</th>
                        <th>名称</th>
                        <th>状态</th>
                        <th>产能</th>
                        <th>位置</th>
                        <th>负责人</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    },

    initEventListeners() {
        // 移除旧的事件监听器，避免重复绑定
        document.removeEventListener('click', this._handleClick);
        
        // 使用箭头函数绑定this
        this._handleClick = (e) => {
            const target = e.target;
            const id = target.id || target.closest('button')?.id;
            
            switch (id) {
                case 'generateBtn':
                    this.handleGenerate();
                    break;
                case 'clearBtn':
                    this.handleClear();
                    break;
                case 'refreshDataBtn':
                    this.handleRefreshData();
                    break;
                case 'uploadBtn':
                    this.handleFileUpload();
                    break;
                case 'createSourceBtn':
                    this.handleCreateDataSource();
                    break;
                case 'generateFromSourceBtn':
                    this.handleGenerateFromSource();
                    break;
            }
        };
        
        document.addEventListener('click', this._handleClick);
    },

    async handleGenerate() {
        try {
            const form = document.getElementById('simulationConfigForm');
            const formData = new FormData(form);
            const config = this.collectConfigFromForm(formData);

            const confirmed = await Modal.confirm('确定要生成模拟数据吗？');
            if (!confirmed) return;

            // 先清除再生成
            await SimulationService.clearSimulationData();
            
            const response = await SimulationService.generateSimulationData(config);
            if (response.code === 200) {
                Toast.success(`生成成功: ${response.data.lines_created}条生产线, ${response.data.equipments_created}个设备`);
                this.loadSimulationStatus();
                this.loadProductionLines();
            } else {
                Toast.error(response.message || '生成失败');
            }
        } catch (error) {
            console.error('生成模拟数据失败:', error);
            Toast.error('生成模拟数据失败');
        }
    },

    async handleClear() {
        const confirmed = await Modal.confirm('确定要清除所有模拟数据吗？');
        if (!confirmed) return;

        const response = await SimulationService.clearSimulationData();
        if (response.code === 200) {
            Toast.success('数据已清除');
            this.loadSimulationStatus();
            this.loadProductionLines();
        }
    },

    async handleRefreshData() {
        await Promise.all([
            this.loadSimulationStatus(),
            this.loadProductionLines(),
            this.loadDataSources()
        ]);
        Toast.success('已刷新');
    },

    async handleFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const dataType = document.getElementById('dataTypeSelect').value;
        const file = fileInput.files[0];

        if (!file) {
            Toast.warning('请选择文件');
            return;
        }

        try {
            let response;
            if (file.name.endsWith('.csv')) {
                response = await SimulationService.importCSV(file, dataType);
            } else if (file.name.endsWith('.json')) {
                response = await SimulationService.importJSON(file, dataType);
            } else {
                Toast.warning('只支持CSV和JSON格式');
                return;
            }

            if (response.code === 200) {
                Toast.success('导入成功');
                this.loadSimulationStatus();
            } else {
                Toast.error(response.message || '导入失败');
            }
        } catch (error) {
            Toast.error('导入失败');
        }
    },

    async handleCreateDataSource() {
        const sourceType = document.getElementById('sourceTypeSelect').value;
        let config = {};

        switch (sourceType) {
            case 'api':
                config = {
                    endpoint: document.getElementById('apiEndpoint').value,
                    method: document.getElementById('apiMethod').value,
                    interval: 5
                };
                break;
            case 'websocket':
                config = {
                    url: document.getElementById('wsUrl').value,
                    interval: 1
                };
                break;
            case 'file_stream':
                config = {
                    format: document.getElementById('fileFormat').value,
                    interval: 10
                };
                break;
            case 'user_input':
                config = {
                    fields: document.getElementById('inputFields').value.split(',').map(f => f.trim())
                };
                break;
        }

        try {
            // 创建模拟数据源
            const response = await SimulationService.createMockDataSource(
                sourceType,
                config
            );

            if (response.code === 200 || response.code === 201) {
                Toast.success('数据源创建成功');
                this.loadDataSources();
            } else {
                Toast.error(response.message || '创建失败');
            }
        } catch (error) {
            console.error('创建数据源失败:', error);
            Toast.error('创建数据源失败');
        }
    },

    async handleGenerateFromSource() {
        if (!this.selectedSourceId) {
            Toast.warning('请先选择一个数据源');
            return;
        }

        const countInput = document.getElementById('generateCount');
        const count = countInput ? parseInt(countInput.value) || 10 : 10;

        try {
            const response = await Request.post(`/center/sources/${this.selectedSourceId}/generate`, {
                count: count
            });

            if (response.code === 200) {
                Toast.success(`成功生成 ${response.data.generated_count || count} 条数据`);
                this.loadSimulationStatus();
                this.loadProductionLines();
            } else {
                Toast.error(response.message || '生成失败');
            }
        } catch (error) {
            console.error('从数据源生成失败:', error);
            Toast.error('生成失败');
        }
    },

    collectConfigFromForm(formData) {
        return {
            lines: {
                count: parseInt(formData.get('lines.count')) || 3,
                status_distribution: { running: 0.6, stopped: 0.2, maintenance: 0.1, error: 0.1 }
            },
            equipments: {
                per_line: parseInt(formData.get('equipments.per_line')) || 3,
                status_distribution: { running: 0.5, idle: 0.3, maintenance: 0.1, error: 0.05, offline: 0.05 }
            },
            sensors: {
                per_equipment: parseInt(formData.get('sensors.per_equipment')) || 4,
                types: ['temperature', 'pressure', 'humidity', 'speed', 'vibration', 'current', 'voltage'],
                type_distribution: { temperature: 0.3, pressure: 0.2, humidity: 0.15, speed: 0.15, vibration: 0.1, current: 0.05, voltage: 0.05 },
                data_distribution: 'normal'
            },
            tasks: {
                count: parseInt(formData.get('tasks.count')) || 10,
                status_distribution: { pending: 0.3, in_progress: 0.4, paused: 0.1, completed: 0.15, cancelled: 0.05 }
            },
            records: {
                days: parseInt(formData.get('records.days')) || 7,
                records_per_day: 100,
                data_distribution: 'normal'
            },
            alerts: {
                probability: 0.05,
                severity_distribution: { info: 0.4, warning: 0.4, error: 0.15, critical: 0.05 }
            }
        };
    }
};

window.SimulationPage = SimulationPage;
