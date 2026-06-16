/**
 * 设备管理页面
 */
const EquipmentPage = {
    currentData: [],
    productionLines: [],

    init() {
        this.render();
        this.loadProductionLines();
        this.initializeSimulation();
        this.loadEquipments();
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">设备管理</h3>
                </div>
                <div class="card-body">
                <div class="toolbar">
                    <div class="toolbar-left">
                        <select class="form-control" id="lineFilter" style="width: 150px;">
                            <option value="">全部生产线</option>
                        </select>
                        <select class="form-control" id="statusFilter" style="width: 120px; margin-left: 8px;">
                            <option value="">全部状态</option>
                            <option value="running">运行中</option>
                            <option value="idle">空闲</option>
                            <option value="maintenance">维护中</option>
                            <option value="error">故障</option>
                            <option value="offline">离线</option>
                        </select>
                        <input type="text" class="form-control" id="searchInput" 
                               placeholder="搜索设备编号或名称..." 
                               style="width: 200px; margin-left: 8px;">
                    </div>
                    <div class="toolbar-right">
                        <div class="data-mode-selector" style="display: inline-flex; align-items: center; margin-right: 12px;">
                            <select class="form-control" id="dataModeSelect" style="width: 120px;">
                                <option value="real">真实数据</option>
                                <option value="simulation">模拟数据</option>
                            </select>
                            <button class="btn btn-outline" id="dataSourceBtn" style="margin-left: 8px; display: none;" title="数据源配置">
                                <span>数据源</span>
                            </button>
                        </div>
                        <button class="btn btn-primary" id="addEquipmentBtn">
                            <span>+ 新增设备</span>
                        </button>
                        <button class="btn btn-outline" id="refreshBtn" style="margin-left: 8px;">
                            <span>刷新</span>
                        </button>
                        <button class="btn btn-outline" id="autoRefreshToggle" style="margin-left: 8px;" title="自动刷新">
                            <span>⏱️ 自动</span>
                        </button>
                    </div>
                </div>
                    <div id="equipmentTable">
                        <div class="loading-container" style="text-align: center; padding: 40px;">
                            <div class="loading-spinner"></div>
                            <div style="margin-top: 10px; color: var(--text-secondary);">加载中...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 绑定事件
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById('lineFilter')?.addEventListener('change', () => this.filterData());
        document.getElementById('statusFilter')?.addEventListener('change', () => this.filterData());
        document.getElementById('searchInput')?.addEventListener('input', () => this.filterData());
        document.getElementById('refreshBtn')?.addEventListener('click', () => this.loadEquipments());
        document.getElementById('addEquipmentBtn')?.addEventListener('click', () => this.showAddModal());
        
        // 数据模式切换
        document.getElementById('dataModeSelect')?.addEventListener('change', () => {
            this.switchDataMode();
        });
        
        // 数据源配置按钮
        document.getElementById('dataSourceBtn')?.addEventListener('click', () => {
            this.showDataSourceConfig();
        });
        
        // 自动刷新开关
        document.getElementById('autoRefreshToggle')?.addEventListener('click', () => {
            this.toggleAutoRefresh();
        });
    },

    async loadProductionLines() {
        try {
            const response = await ProductionService.getLines({ size: 100 });
            if (response.code === 200) {
                this.productionLines = response.data.items || response.data.list || [];
                this.updateLineFilter();
            }
        } catch (error) {
            console.error('加载生产线失败:', error);
        }
    },

    updateLineFilter() {
        const select = document.getElementById('lineFilter');
        if (!select) return;

        const options = this.productionLines.map(line => 
            `<option value="${line.id}">${line.line_name || line.line_code}</option>`
        ).join('');
        
        select.innerHTML = `<option value="">全部生产线</option>${options}`;
    },

    async loadEquipments() {
        const tableContainer = document.getElementById('equipmentTable');
        
        try {
            const response = await ProductionService.getEquipments({ size: 100 });
            
            if (response.code === 200) {
                this.currentData = response.data.items || [];
                this.renderTable(this.currentData);
            } else {
                tableContainer.innerHTML = `
                    <div class="error-state" style="text-align: center; padding: 40px; color: var(--danger-color);">
                        <div style="font-size: 48px;">⚠️</div>
                        <div>${response.message || '加载失败'}</div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载设备失败:', error);
            tableContainer.innerHTML = `
                <div class="error-state" style="text-align: center; padding: 40px; color: var(--danger-color);">
                    <div style="font-size: 48px;">❌</div>
                    <div>加载设备失败: ${error.message}</div>
                    <button class="btn btn-primary" onclick="EquipmentPage.loadEquipments()" style="margin-top: 16px;">重试</button>
                </div>
            `;
        }
    },

    renderTable(equipments) {
        const container = document.getElementById('equipmentTable');
        
        if (!equipments || equipments.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 60px; color: var(--text-secondary);">
                    <div style="font-size: 64px; margin-bottom: 16px;">📦</div>
                    <div style="font-size: 18px; margin-bottom: 8px;">暂无设备数据</div>
                    <div style="font-size: 14px;">点击"新增设备"添加第一个设备</div>
                </div>
            `;
            return;
        }

        const rows = equipments.map(eq => this.renderRow(eq)).join('');
        
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>设备编号</th>
                        <th>设备名称</th>
                        <th>类型</th>
                        <th>所属生产线</th>
                        <th>温度(℃)</th>
                        <th>压力(MPa)</th>
                        <th>速度(rpm)</th>
                        <th>运行时长</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
            <div class="table-footer" style="margin-top: 16px; color: var(--text-secondary); font-size: 14px;">
                共 ${equipments.length} 条记录
            </div>
        `;
    },

    renderRow(eq) {
        const line = this.productionLines.find(l => l.id === eq.line_id);
        const lineName = line ? (line.line_name || line.line_code) : '-';
        
        return `
            <tr>
                <td>${eq.equipment_code || '-'}</td>
                <td>${eq.equipment_name || '-'}</td>
                <td>${eq.equipment_type || '-'}</td>
                <td>${lineName}</td>
                <td>${eq.temperature ? parseFloat(eq.temperature).toFixed(1) : '-'}</td>
                <td>${eq.pressure ? parseFloat(eq.pressure).toFixed(2) : '-'}</td>
                <td>${eq.speed ? parseFloat(eq.speed).toFixed(0) : '-'}</td>
                <td>${eq.runtime_hours ? parseFloat(eq.runtime_hours).toFixed(1) + 'h' : '-'}</td>
                <td><span class="status-badge ${eq.status}">${this.getStatusText(eq.status)}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="EquipmentPage.showDetail(${eq.id})">详情</button>
                    <button class="btn btn-sm btn-success" onclick="EquipmentPage.controlEquipment(${eq.id}, 'start')">启动</button>
                    <button class="btn btn-sm btn-warning" onclick="EquipmentPage.controlEquipment(${eq.id}, 'stop')">停止</button>
                </td>
            </tr>
        `;
    },

    getStatusText(status) {
        const map = {
            running: '运行中',
            idle: '空闲',
            maintenance: '维护中',
            error: '故障',
            offline: '离线'
        };
        return map[status] || status;
    },

    filterData() {
        const lineId = document.getElementById('lineFilter')?.value;
        const status = document.getElementById('statusFilter')?.value;
        const search = document.getElementById('searchInput')?.value?.toLowerCase() || '';

        let filtered = this.currentData;

        if (lineId) {
            filtered = filtered.filter(eq => eq.line_id == lineId);
        }
        if (status) {
            filtered = filtered.filter(eq => eq.status === status);
        }
        if (search) {
            filtered = filtered.filter(eq => 
                (eq.equipment_code && eq.equipment_code.toLowerCase().includes(search)) ||
                (eq.equipment_name && eq.equipment_name.toLowerCase().includes(search))
            );
        }

        this.renderTable(filtered);
    },

    async showAddModal() {
        const lineOptions = this.productionLines.map(line => 
            `<option value="${line.id}">${line.line_name || line.line_code}</option>`
        ).join('');

        const result = await Modal.form('新增设备', `
            <div class="form-group">
                <label>设备编号 <span style="color: red;">*</span></label>
                <input type="text" class="form-control" name="equipment_code" required placeholder="如: EQP-001">
            </div>
            <div class="form-group">
                <label>设备名称 <span style="color: red;">*</span></label>
                <input type="text" class="form-control" name="equipment_name" required placeholder="如: 包装机">
            </div>
            <div class="form-group">
                <label>设备类型</label>
                <input type="text" class="form-control" name="equipment_type" placeholder="如: 包装设备">
            </div>
            <div class="form-group">
                <label>所属生产线 <span style="color: red;">*</span></label>
                <select class="form-control" name="line_id" required>
                    <option value="">请选择生产线</option>
                    ${lineOptions}
                </select>
            </div>
            <div class="form-group">
                <label>型号</label>
                <input type="text" class="form-control" name="model" placeholder="如: MODEL-100">
            </div>
            <div class="form-group">
                <label>制造商</label>
                <input type="text" class="form-control" name="manufacturer" placeholder="如: 厂商A">
            </div>
        `);

        if (result) {
            await this.createEquipment(result);
        }
    },

    async createEquipment(data) {
        try {
            const response = await ProductionService.createEquipment(data);
            if (response.code === 200 || response.code === 201) {
                Toast.success('设备创建成功');
                this.loadEquipments();
            } else {
                Toast.error(response.message || '创建失败');
            }
        } catch (error) {
            console.error('创建设备失败:', error);
            Toast.error('创建设备失败');
        }
    },

    async showDetail(id) {
        try {
            const response = await ProductionService.getEquipmentById(id);
            if (response.code === 200) {
                const eq = response.data;
                const line = this.productionLines.find(l => l.id === eq.line_id);
                
                const sensorsHtml = (eq.sensors || []).map(s => `
                    <tr>
                        <td>${s.sensor_code || '-'}</td>
                        <td>${s.sensor_name || '-'}</td>
                        <td>${s.sensor_type || '-'}</td>
                        <td>${s.current_value || '-'}</td>
                        <td><span class="status-badge ${s.status}">${s.status || '-'}</span></td>
                    </tr>
                `).join('') || '<tr><td colspan="5" style="text-align: center;">暂无传感器</td></tr>';

                await Modal.alert(`
                    <div class="detail-section">
                        <h4>基本信息</h4>
                        <table class="detail-table">
                            <tr><td>设备编号</td><td>${eq.equipment_code}</td></tr>
                            <tr><td>设备名称</td><td>${eq.equipment_name}</td></tr>
                            <tr><td>设备类型</td><td>${eq.equipment_type || '-'}</td></tr>
                            <tr><td>所属生产线</td><td>${line ? (line.line_name || line.line_code) : '-'}</td></tr>
                            <tr><td>型号</td><td>${eq.model || '-'}</td></tr>
                            <tr><td>制造商</td><td>${eq.manufacturer || '-'}</td></tr>
                            <tr><td>状态</td><td><span class="status-badge ${eq.status}">${this.getStatusText(eq.status)}</span></td></tr>
                        </table>
                    </div>
                    <div class="detail-section" style="margin-top: 20px;">
                        <h4>运行参数</h4>
                        <table class="detail-table">
                            <tr><td>温度</td><td>${eq.temperature ? parseFloat(eq.temperature).toFixed(2) + ' ℃' : '-'}</td></tr>
                            <tr><td>压力</td><td>${eq.pressure ? parseFloat(eq.pressure).toFixed(2) + ' MPa' : '-'}</td></tr>
                            <tr><td>速度</td><td>${eq.speed ? parseFloat(eq.speed).toFixed(2) + ' rpm' : '-'}</td></tr>
                            <tr><td>运行时长</td><td>${eq.runtime_hours ? parseFloat(eq.runtime_hours).toFixed(1) + ' 小时' : '-'}</td></tr>
                        </table>
                    </div>
                    <div class="detail-section" style="margin-top: 20px;">
                        <h4>传感器列表</h4>
                        <table class="data-table">
                            <thead><tr><th>编号</th><th>名称</th><th>类型</th><th>当前值</th><th>状态</th></tr></thead>
                            <tbody>${sensorsHtml}</tbody>
                        </table>
                    </div>
                `, '设备详情');
            } else {
                Toast.error(response.message || '获取详情失败');
            }
        } catch (error) {
            console.error('获取设备详情失败:', error);
            Toast.error('获取设备详情失败');
        }
    },

    async controlEquipment(id, action) {
        try {
            const response = await ProductionService.controlEquipment(id, action);
            if (response.code === 200) {
                Toast.success(`${action === 'start' ? '启动' : '停止'}成功`);
                this.loadEquipments();
            } else {
                Toast.error(response.message || '操作失败');
            }
        } catch (error) {
            console.error('控制设备失败:', error);
            Toast.error('控制设备失败');
        }
    },

    // ==================== 模拟数据功能 ====================

    async initializeSimulation() {
        try {
            // 检查EquipmentSimulationService是否可用
            if (typeof window.EquipmentSimulationService === 'undefined') {
                console.warn('EquipmentSimulationService未加载，使用真实数据模式');
                return;
            }

            // 初始化模拟环境
            const result = await EquipmentSimulationService.initializeSimulationEnvironment();
            if (!result.success) {
                console.warn('模拟环境初始化失败:', result.error);
            }

            // 设置当前数据模式
            const currentMode = EquipmentSimulationService.getCurrentDataMode();
            const dataModeSelect = document.getElementById('dataModeSelect');
            if (dataModeSelect) {
                dataModeSelect.value = currentMode;
                this.updateUIForDataMode(currentMode);
            }

        } catch (error) {
            console.error('初始化模拟功能失败:', error);
        }
    },

    updateUIForDataMode(mode) {
        const dataSourceBtn = document.getElementById('dataSourceBtn');
        if (mode === 'simulation') {
            dataSourceBtn.style.display = 'inline-block';
        } else {
            dataSourceBtn.style.display = 'none';
        }
    },

    async switchDataMode() {
        const dataModeSelect = document.getElementById('dataModeSelect');
        if (!dataModeSelect) return;

        const mode = dataModeSelect.value;
        this.updateUIForDataMode(mode);

        // 保存模式选择
        if (typeof window.EquipmentSimulationService !== 'undefined') {
            const sourceIds = EquipmentSimulationService.getSavedDataSources();
            await EquipmentSimulationService.switchDataMode(mode === 'simulation', sourceIds);
        }

        // 重新加载数据
        this.loadEquipments();
    },

    async loadEquipments() {
        const tableContainer = document.getElementById('equipmentTable');
        const dataModeSelect = document.getElementById('dataModeSelect');
        const currentMode = dataModeSelect ? dataModeSelect.value : 'real';
        
        try {
            let response;
            
            if (currentMode === 'simulation' && typeof window.EquipmentSimulationService !== 'undefined') {
                // 使用模拟数据
                const params = {
                    page: 1,
                    size: 100,
                    useRealData: false
                };
                
                // 获取筛选参数
                const lineId = document.getElementById('lineFilter')?.value;
                const status = document.getElementById('statusFilter')?.value;
                
                if (lineId) params.lineId = lineId;
                if (status) params.status = status;
                
                // 获取保存的数据源
                const sourceIds = EquipmentSimulationService.getSavedDataSources();
                if (sourceIds.length > 0) {
                    params.sourceIds = sourceIds;
                }
                
                response = await EquipmentSimulationService.getSimulationData(params);
                
            } else {
                // 使用真实数据
                response = await ProductionService.getEquipments({ size: 100 });
            }
            
            if (response.code === 200) {
                const data = response.data;
                
                // 处理分页数据和普通数据
                if (data.items && data.total !== undefined) {
                    // 分页格式数据
                    this.currentData = data.items || [];
                } else {
                    // 普通数组格式数据
                    this.currentData = Array.isArray(data) ? data : [];
                }
                
                this.renderTable(this.currentData);
            } else {
                tableContainer.innerHTML = `
                    <div class="error-state" style="text-align: center; padding: 40px; color: var(--danger-color);">
                        <div style="font-size: 48px;">⚠️</div>
                        <div>${response.message || '加载失败'}</div>
                        <button class="btn btn-primary" onclick="EquipmentPage.loadEquipments()" style="margin-top: 16px;">重试</button>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载设备失败:', error);
            tableContainer.innerHTML = `
                <div class="error-state" style="text-align: center; padding: 40px; color: var(--danger-color);">
                    <div style="font-size: 48px;">❌</div>
                    <div>加载设备失败: ${error.message}</div>
                    <button class="btn btn-primary" onclick="EquipmentPage.loadEquipments()" style="margin-top: 16px;">重试</button>
                </div>
            `;
        }
    },

    async showDataSourceConfig() {
        try {
            // 获取可用数据源
            const sourcesRes = await EquipmentSimulationService.listDataSources();
            let availableSources = [];
            if (sourcesRes.code === 200) {
                availableSources = sourcesRes.data.sources || [];
            }

            // 获取已选择的数据源
            const savedSources = EquipmentSimulationService.getSavedDataSources();

            // 创建数据源选择界面
            const sourcesHtml = availableSources.map(source => {
                const isSelected = savedSources.includes(source.source_id);
                return `
                    <div class="data-source-item" style="margin-bottom: 12px; padding: 12px; border: 1px solid var(--border-color); border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h5 style="margin: 0;">${source.source_id}</h5>
                                <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                                    类型: ${source.type} | 状态: ${source.status}
                                </div>
                            </div>
                            <div>
                                <input type="checkbox" id="source_${source.source_id}" 
                                       ${isSelected ? 'checked' : ''} 
                                       style="transform: scale(1.2);">
                            </div>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                            ${source.description || '无描述'}
                        </div>
                    </div>
                `;
            }).join('') || '<div style="text-align: center; padding: 20px; color: var(--text-secondary);">暂无可用数据源</div>';

            const result = await Modal.form('数据源配置', `
                <div class="form-section" style="margin-bottom: 20px;">
                    <h4>选择数据源</h4>
                    <div style="max-height: 300px; overflow-y: auto; margin-top: 12px;">
                        ${sourcesHtml}
                    </div>
                </div>
                <div class="form-section">
                    <h4>创建新数据源</h4>
                    <div class="form-group">
                        <label>数据源类型</label>
                        <select class="form-control" name="new_source_type">
                            <option value="api">API数据源</option>
                            <option value="websocket">WebSocket数据源</option>
                            <option value="file_stream">文件流数据源</option>
                            <option value="user_input">用户输入数据源</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>数据源名称</label>
                        <input type="text" class="form-control" name="new_source_name" placeholder="如: 生产线1模拟数据源">
                    </div>
                    <div class="form-group">
                        <label>刷新间隔（秒）</label>
                        <input type="number" class="form-control" name="new_source_interval" value="5" min="1" max="300">
                    </div>
                </div>
            `, { width: '600px' });

            if (result) {
                // 1. 更新选中的数据源
                const selectedSources = availableSources
                    .filter(source => document.getElementById(`source_${source.source_id}`)?.checked)
                    .map(source => source.source_id);

                // 保存选中的数据源
                Storage.set('equipment_data_sources', JSON.stringify(selectedSources));

                // 2. 如果提供了新数据源配置，创建新数据源
                if (result.new_source_name && result.new_source_type) {
                    const config = {
                        name: result.new_source_name,
                        interval: parseInt(result.new_source_interval) || 5
                    };
                    
                    await EquipmentSimulationService.createDataSource(result.new_source_type, config);
                    Toast.success('数据源创建成功');
                }

                Toast.success('数据源配置已保存');
                // 重新加载数据
                this.loadEquipments();
            }

        } catch (error) {
            console.error('配置数据源失败:', error);
            Toast.error('配置数据源失败');
        }
    },

    async toggleAutoRefresh() {
        const toggleBtn = document.getElementById('autoRefreshToggle');
        const isActive = toggleBtn.classList.contains('active');
        
        try {
            if (isActive) {
                // 停止自动刷新
                await EquipmentSimulationService.stopAutoRefresh();
                toggleBtn.classList.remove('active');
                toggleBtn.innerHTML = '<span>⏱️ 自动</span>';
                Toast.info('自动刷新已停止');
            } else {
                // 启动自动刷新
                await EquipmentSimulationService.startAutoRefresh(30);
                toggleBtn.classList.add('active');
                toggleBtn.innerHTML = '<span>⏱️ 刷新中</span>';
                Toast.success('自动刷新已启动，间隔30秒');
            }
        } catch (error) {
            console.error('切换自动刷新失败:', error);
            Toast.error('切换自动刷新失败');
        }
    },

    // ==================== 辅助方法 ====================

    getStatusText(status) {
        const map = {
            running: '运行中',
            idle: '空闲',
            maintenance: '维护中',
            error: '故障',
            offline: '离线'
        };
        return map[status] || status;
    }
};

window.EquipmentPage = EquipmentPage;
