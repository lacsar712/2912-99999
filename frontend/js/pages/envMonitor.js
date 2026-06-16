/**
 * 环境监测页面
 */
const EnvMonitorPage = {
    currentTab: 'dashboard',
    refreshInterval: null,
    historyChart: null,
    currentAreaId: null,
    selectedItems: ['温度', '湿度', 'PM2.5', 'CO2', '噪音'],
    timeWindow: '1h',

    init() {
        this.render();
        this.loadDashboard();
        // 每30秒自动刷新实时数据
        this.refreshInterval = setInterval(() => {
            if (this.currentTab === 'dashboard') {
                this.loadDashboard();
            }
        }, 30000);
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="env-monitor-container">
                <!-- 统计卡片 -->
                <div class="stat-cards" id="statsCards">
                    <div class="stat-card">
                        <div class="stat-card-icon primary">📍</div>
                        <div class="stat-card-title">区域</div>
                        <div class="stat-card-value"><span class="loading-text">加载中...</span></div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-icon success">📡</div>
                        <div class="stat-card-title">监测点</div>
                        <div class="stat-card-value"><span class="loading-text">加载中...</span></div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-icon warning">⚠️</div>
                        <div class="stat-card-title">今日异常</div>
                        <div class="stat-card-value"><span class="loading-text">加载中...</span></div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-icon danger">🔔</div>
                        <div class="stat-card-title">活跃告警</div>
                        <div class="stat-card-value"><span class="loading-text">加载中...</span></div>
                    </div>
                </div>

                <!-- 标签栏 -->
                <div class="safety-tab-bar">
                    <div class="safety-tab active" data-tab="dashboard" onclick="EnvMonitorPage.switchTab('dashboard')">
                        📊 实时大屏
                    </div>
                    <div class="safety-tab" data-tab="areas" onclick="EnvMonitorPage.switchTab('areas')">
                        🌳 区域管理
                    </div>
                    <div class="safety-tab" data-tab="points" onclick="EnvMonitorPage.switchTab('points')">
                        📍 监测点配置
                    </div>
                    <div class="safety-tab" data-tab="history" onclick="EnvMonitorPage.switchTab('history')">
                        📈 历史趋势
                    </div>
                    <div class="safety-tab" data-tab="standards" onclick="EnvMonitorPage.switchTab('standards')">
                        ⚙️ 阈值配置
                    </div>
                </div>

                <!-- 内容区域 -->
                <div class="tab-content" id="tabContent">
                    <div class="loading">加载中...</div>
                </div>
            </div>
        `;

        this.loadStatistics();
    },

    async loadStatistics() {
        try {
            const response = await EnvMonitorService.getStatistics();
            if (response.code === 200) {
                const data = response.data;
                const cards = document.querySelectorAll('#statsCards .stat-card');
                if (cards[0]) cards[0].querySelector('.stat-card-value').textContent = data.total_areas;
                if (cards[1]) cards[1].querySelector('.stat-card-value').textContent = `${data.active_points}/${data.total_points}`;
                if (cards[2]) {
                    const el = cards[2].querySelector('.stat-card-value');
                    el.textContent = data.today_abnormal;
                    if (data.today_abnormal > 0) el.style.color = 'var(--warning-color)';
                }
                if (cards[3]) {
                    const el = cards[3].querySelector('.stat-card-value');
                    el.textContent = data.active_alerts;
                    if (data.active_alerts > 0) el.style.color = 'var(--danger-color)';
                }
            }
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },

    switchTab(tab) {
        this.currentTab = tab;
        
        document.querySelectorAll('.safety-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });

        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        if (tab === 'dashboard') {
            this.loadDashboard();
            this.refreshInterval = setInterval(() => this.loadDashboard(), 30000);
        } else if (tab === 'areas') {
            this.loadAreaManagement();
        } else if (tab === 'points') {
            this.loadMonitorPoints();
        } else if (tab === 'history') {
            this.loadHistoryTrend();
        } else if (tab === 'standards') {
            this.loadStandards();
        }
    },

    // ==================== 实时大屏 ====================

    async loadDashboard() {
        const container = document.getElementById('tabContent');
        try {
            const response = await EnvMonitorService.getRealtimeReadings();
            if (response.code === 200) {
                this.renderDashboard(response.data);
            }
        } catch (error) {
            console.error('加载实时数据失败:', error);
            container.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">加载实时数据失败</div></div>';
        }
    },

    renderDashboard(data) {
        const container = document.getElementById('tabContent');
        
        if (!data || Object.keys(data).length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📡</div>
                    <div class="empty-text">暂无监测数据</div>
                    <p>请先在"区域管理"和"监测点配置"中创建区域和监测点</p>
                    <button class="btn btn-primary" onclick="EnvMonitorPage.switchTab('areas')">去配置</button>
                </div>
            `;
            return;
        }

        let html = '<div class="grid grid-2">';
        
        for (const [areaKey, areaData] of Object.entries(data)) {
            const hasWarning = Object.values(areaData.points).some(p => 
                Object.values(p.items).some(i => i.status === 'warning' || i.status === 'danger')
            );
            
            html += `
                <div class="card env-area-panel ${hasWarning ? 'panel-warning' : ''}">
                    <div class="card-header">
                        <h3 class="card-title">
                            ${hasWarning ? '<span class="alert-dot"></span>' : ''}
                            ${Validator.sanitize(areaData.area_name)}
                        </h3>
                        <span class="status-badge ${hasWarning ? 'error' : 'running'}">
                            ${hasWarning ? '有告警' : '正常'}
                        </span>
                    </div>
                    <div class="card-body">
                        <div class="env-gauges-grid">
            `;
            
            for (const [pointKey, pointData] of Object.entries(areaData.points)) {
                for (const [itemName, itemData] of Object.entries(pointData.items)) {
                    const isAbnormal = itemData.status === 'warning' || itemData.status === 'danger';
                    const statusClass = isAbnormal ? 'abnormal' : 'normal';
                    const displayValue = itemData.value !== null ? itemData.value.toFixed(1) : '--';
                    
                    html += `
                        <div class="env-gauge ${statusClass}" title="${itemData.status_msg || ''}">
                            ${isAbnormal ? '<span class="gauge-alert-dot"></span>' : ''}
                            <div class="gauge-title">${Validator.sanitize(itemName)}</div>
                            <div class="gauge-value">${displayValue}<span class="gauge-unit">${Validator.sanitize(itemData.unit || '')}</span></div>
                            <div class="gauge-point">${Validator.sanitize(pointData.point_name)}</div>
                            ${itemData.standard ? `
                                <div class="gauge-range">
                                    ${itemData.standard.alert_low !== null ? `低: ${itemData.standard.alert_low}` : ''}
                                    ${itemData.standard.alert_high !== null ? `高: ${itemData.standard.alert_high}` : ''}
                                </div>
                            ` : ''}
                        </div>
                    `;
                }
            }
            
            html += `
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        
        // 添加操作按钮
        html += `
            <div class="card" style="margin-top: 16px;">
                <div class="card-body" style="display: flex; justify-content: flex-end; gap: 12px;">
                    <button class="btn btn-outline" onclick="EnvMonitorPage.loadDashboard()">
                        🔄 刷新数据
                    </button>
                    <button class="btn btn-primary" onclick="EnvMonitorPage.generateMockData()">
                        🧪 生成模拟数据
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    },

    async generateMockData() {
        try {
            const response = await EnvMonitorService.generateSimulatedReadings({
                interval: 5,
                abnormal_probability: 0.1
            });
            if (response.code === 200) {
                Toast.success(response.message);
                this.loadStatistics();
                this.loadDashboard();
            } else {
                Toast.error(response.message);
            }
        } catch (error) {
            console.error('生成模拟数据失败:', error);
            Toast.error('生成模拟数据失败');
        }
    },

    // ==================== 区域管理 ====================

    async loadAreaManagement() {
        const container = document.getElementById('tabContent');
        try {
            const [treeResponse, listResponse] = await Promise.all([
                EnvMonitorService.getAreaTree(),
                EnvMonitorService.getAreas({ page: 1, size: 100 })
            ]);
            
            if (treeResponse.code === 200) {
                this.renderAreaManagement(treeResponse.data, listResponse.data?.items || []);
            }
        } catch (error) {
            console.error('加载区域数据失败:', error);
            container.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">加载区域数据失败</div></div>';
        }
    },

    renderAreaManagement(treeData, areas) {
        const container = document.getElementById('tabContent');
        
        container.innerHTML = `
            <div class="knowledge-container">
                <div class="knowledge-sidebar">
                    <div class="knowledge-sidebar-header">
                        <h3>区域树</h3>
                        <button class="btn btn-sm btn-primary" onclick="EnvMonitorPage.showAreaModal()">+ 新增</button>
                    </div>
                    <div class="knowledge-category-tree" id="areaTree">
                        ${this.renderTreeItems(treeData)}
                    </div>
                </div>
                <div class="knowledge-main">
                    <div class="knowledge-toolbar">
                        <div class="toolbar-left">
                            <span>共 ${areas.length} 个区域</span>
                        </div>
                        <div class="toolbar-right">
                            <button class="btn btn-sm btn-primary" onclick="EnvMonitorPage.showAreaModal()">+ 新增区域</button>
                        </div>
                    </div>
                    <div class="knowledge-content">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>区域编码</th>
                                    <th>区域名称</th>
                                    <th>区域类型</th>
                                    <th>上级区域</th>
                                    <th>状态</th>
                                    <th>排序</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="areaTableBody">
                                ${areas.map(area => this.renderAreaRow(area)).join('')}
                            </tbody>
                        </table>
                        ${areas.length === 0 ? '<div class="empty-state"><div class="empty-icon">📍</div><div class="empty-text">暂无区域数据</div></div>' : ''}
                    </div>
                </div>
            </div>
        `;
    },

    renderTreeItems(items, level = 0) {
        if (!items || items.length === 0) return '';
        
        return items.map(item => `
            <div class="tree-item" data-id="${item.id}" style="padding-left: ${level * 16 + 8}px;">
                <span class="tree-toggle">${item.children && item.children.length > 0 ? '▼' : '•'}</span>
                <span class="tree-item-name">${Validator.sanitize(item.area_name)}</span>
                <span class="tree-item-actions">
                    <button class="tree-action-btn" onclick="event.stopPropagation(); EnvMonitorPage.showAreaModal(${item.id})">✏️</button>
                    <button class="tree-action-btn" onclick="event.stopPropagation(); EnvMonitorPage.deleteArea(${item.id})">🗑️</button>
                </span>
            </div>
            ${item.children && item.children.length > 0 ? this.renderTreeItems(item.children, level + 1) : ''}
        `).join('');
    },

    renderAreaRow(area) {
        const typeMap = {
            'workshop': '车间',
            'warehouse': '仓库',
            'office': '办公区',
            'other': '其他'
        };
        
        return `
            <tr>
                <td>${Validator.sanitize(area.area_code)}</td>
                <td>${Validator.sanitize(area.area_name)}</td>
                <td>${typeMap[area.area_type] || area.area_type}</td>
                <td>${Validator.sanitize(area.parent_name || '-')}</td>
                <td><span class="status-badge ${area.is_active ? 'running' : 'stopped'}">${area.is_active ? '启用' : '禁用'}</span></td>
                <td>${area.sort_order}</td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="EnvMonitorPage.showAreaModal(${area.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="EnvMonitorPage.deleteArea(${area.id})">删除</button>
                </td>
            </tr>
        `;
    },

    async showAreaModal(id = null) {
        let area = null;
        let areas = [];
        
        try {
            const [areaResponse, areasResponse] = await Promise.all([
                id ? EnvMonitorService.getArea(id) : Promise.resolve({ data: null }),
                EnvMonitorService.getAreas({ page: 1, size: 100 })
            ]);
            
            if (areaResponse.data) area = areaResponse.data;
            if (areasResponse.data?.items) areas = areasResponse.data.items;
        } catch (error) {
            console.error('获取区域数据失败:', error);
        }
        
        const title = id ? '编辑区域' : '新增区域';
        const content = `
            <form id="areaForm">
                <div class="form-group">
                    <label>区域编码 *</label>
                    <input type="text" class="form-input" name="area_code" value="${area?.area_code || ''}" required>
                </div>
                <div class="form-group">
                    <label>区域名称 *</label>
                    <input type="text" class="form-input" name="area_name" value="${area?.area_name || ''}" required>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>区域类型</label>
                        <select class="form-input" name="area_type">
                            <option value="workshop" ${area?.area_type === 'workshop' ? 'selected' : ''}>车间</option>
                            <option value="warehouse" ${area?.area_type === 'warehouse' ? 'selected' : ''}>仓库</option>
                            <option value="office" ${area?.area_type === 'office' ? 'selected' : ''}>办公区</option>
                            <option value="other" ${area?.area_type === 'other' ? 'selected' : ''}>其他</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>上级区域</label>
                        <select class="form-input" name="parent_id">
                            <option value="">无</option>
                            ${areas.filter(a => a.id !== id).map(a => `
                                <option value="${a.id}" ${area?.parent_id === a.id ? 'selected' : ''}>
                                    ${Validator.sanitize(a.area_name)}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>排序</label>
                        <input type="number" class="form-input" name="sort_order" value="${area?.sort_order || 0}">
                    </div>
                    <div class="form-group">
                        <label>状态</label>
                        <select class="form-input" name="is_active">
                            <option value="true" ${area?.is_active !== false ? 'selected' : ''}>启用</option>
                            <option value="false" ${area?.is_active === false ? 'selected' : ''}>禁用</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>描述</label>
                    <textarea class="form-input" name="description" rows="3">${area?.description || ''}</textarea>
                </div>
            </form>
        `;
        
        Modal.show({
            title,
            content,
            onConfirm: async () => {
                const form = document.getElementById('areaForm');
                const formData = new FormData(form);
                const data = {
                    area_code: formData.get('area_code'),
                    area_name: formData.get('area_name'),
                    area_type: formData.get('area_type'),
                    parent_id: formData.get('parent_id') ? parseInt(formData.get('parent_id')) : null,
                    sort_order: parseInt(formData.get('sort_order')) || 0,
                    is_active: formData.get('is_active') === 'true',
                    description: formData.get('description')
                };
                
                try {
                    let response;
                    if (id) {
                        response = await EnvMonitorService.updateArea(id, data);
                    } else {
                        response = await EnvMonitorService.createArea(data);
                    }
                    
                    if (response.code === 200) {
                        Toast.success(response.message);
                        Modal.hide();
                        this.loadStatistics();
                        this.loadAreaManagement();
                    } else {
                        Toast.error(response.message);
                    }
                } catch (error) {
                    console.error('保存区域失败:', error);
                    Toast.error('保存失败');
                }
                return false;
            }
        });
    },

    async deleteArea(id) {
        const confirmed = await Modal.confirm('确定要删除该区域吗？删除后无法恢复。');
        if (!confirmed) return;
        
        try {
            const response = await EnvMonitorService.deleteArea(id);
            if (response.code === 200) {
                Toast.success(response.message);
                this.loadStatistics();
                this.loadAreaManagement();
            } else {
                Toast.error(response.message);
            }
        } catch (error) {
            console.error('删除区域失败:', error);
            Toast.error('删除失败');
        }
    },

    // ==================== 监测点配置 ====================

    async loadMonitorPoints() {
        const container = document.getElementById('tabContent');
        try {
            const [pointsResponse, areasResponse] = await Promise.all([
                EnvMonitorService.getMonitorPoints({ page: 1, size: 100 }),
                EnvMonitorService.getAreas({ page: 1, size: 100 })
            ]);
            
            if (pointsResponse.code === 200) {
                this.renderMonitorPoints(
                    pointsResponse.data?.items || [],
                    areasResponse.data?.items || []
                );
            }
        } catch (error) {
            console.error('加载监测点失败:', error);
            container.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">加载监测点失败</div></div>';
        }
    },

    renderMonitorPoints(points, areas) {
        const container = document.getElementById('tabContent');
        
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">监测点配置</h3>
                    <button class="btn btn-sm btn-primary" onclick="EnvMonitorPage.showPointModal()">+ 新增监测点</button>
                </div>
                <div class="card-body">
                    <div class="table-toolbar">
                        <div class="toolbar-filters">
                            <select class="form-input" style="width: 200px;" onchange="EnvMonitorPage.filterPointsByArea(this.value)">
                                <option value="">全部区域</option>
                                ${areas.map(a => `<option value="${a.id}">${Validator.sanitize(a.area_name)}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    <table class="data-table" id="pointsTable">
                        <thead>
                            <tr>
                                <th>监测点编号</th>
                                <th>监测点名称</th>
                                <th>关联区域</th>
                                <th>监测项目</th>
                                <th>位置</th>
                                <th>状态</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="pointsTableBody">
                            ${points.map(p => this.renderPointRow(p)).join('')}
                        </tbody>
                    </table>
                    ${points.length === 0 ? '<div class="empty-state"><div class="empty-icon">📡</div><div class="empty-text">暂无监测点</div></div>' : ''}
                </div>
            </div>
        `;
    },

    renderPointRow(point) {
        const items = point.monitor_items || [];
        const itemNames = items.map(i => `${i.name}(${i.unit})`).join(', ');
        
        return `
            <tr>
                <td>${Validator.sanitize(point.point_code)}</td>
                <td>${Validator.sanitize(point.point_name)}</td>
                <td>${Validator.sanitize(point.area_name || '-')}</td>
                <td><span class="text-truncate" style="max-width: 200px;" title="${Validator.sanitize(itemNames)}">${Validator.sanitize(itemNames)}</span></td>
                <td>${Validator.sanitize(point.location || '-')}</td>
                <td><span class="status-badge ${point.point_status === 'active' ? 'running' : point.point_status === 'maintenance' ? 'maintenance' : 'stopped'}">
                    ${point.point_status === 'active' ? '运行' : point.point_status === 'maintenance' ? '维护' : '停用'}
                </span></td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="EnvMonitorPage.showPointModal(${point.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="EnvMonitorPage.deletePoint(${point.id})">删除</button>
                </td>
            </tr>
        `;
    },

    async filterPointsByArea(areaId) {
        try {
            const params = areaId ? { areaId, page: 1, size: 100 } : { page: 1, size: 100 };
            const response = await EnvMonitorService.getMonitorPoints(params);
            if (response.code === 200) {
                const tbody = document.getElementById('pointsTableBody');
                if (tbody) {
                    const points = response.data?.items || [];
                    tbody.innerHTML = points.map(p => this.renderPointRow(p)).join('');
                }
            }
        } catch (error) {
            console.error('筛选监测点失败:', error);
        }
    },

    monitorItems: [],

    async showPointModal(id = null) {
        let point = null;
        let areas = [];
        this.monitorItems = [];
        
        try {
            const [pointResponse, areasResponse] = await Promise.all([
                id ? EnvMonitorService.getMonitorPoint(id) : Promise.resolve({ data: null }),
                EnvMonitorService.getAreas({ page: 1, size: 100 })
            ]);
            
            if (pointResponse.data) point = pointResponse.data;
            if (areasResponse.data?.items) areas = areasResponse.data.items;
            if (point?.monitor_items) this.monitorItems = [...point.monitor_items];
        } catch (error) {
            console.error('获取监测点数据失败:', error);
        }
        
        const title = id ? '编辑监测点' : '新增监测点';
        const content = `
            <form id="pointForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>监测点编号 *</label>
                        <input type="text" class="form-input" name="point_code" value="${point?.point_code || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>监测点名称 *</label>
                        <input type="text" class="form-input" name="point_name" value="${point?.point_name || ''}" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>关联区域 *</label>
                        <select class="form-input" name="area_id" required>
                            <option value="">请选择区域</option>
                            ${areas.map(a => `
                                <option value="${a.id}" ${point?.area_id === a.id ? 'selected' : ''}>
                                    ${Validator.sanitize(a.area_name)}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>状态</label>
                        <select class="form-input" name="point_status">
                            <option value="active" ${point?.point_status === 'active' ? 'selected' : ''}>运行</option>
                            <option value="inactive" ${point?.point_status === 'inactive' ? 'selected' : ''}>停用</option>
                            <option value="maintenance" ${point?.point_status === 'maintenance' ? 'selected' : ''}>维护</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>位置描述</label>
                    <input type="text" class="form-input" name="location" value="${point?.location || ''}" placeholder="如：车间A-东南角">
                </div>
                <div class="form-group">
                    <label>监测项目</label>
                    <div id="monitorItemsContainer">
                        ${this.renderMonitorItemsList()}
                    </div>
                    <button type="button" class="btn btn-sm btn-outline" onclick="EnvMonitorPage.addMonitorItem()" style="margin-top: 8px;">
                        + 添加项目
                    </button>
                </div>
                <div class="form-group">
                    <label>备注</label>
                    <textarea class="form-input" name="description" rows="2">${point?.description || ''}</textarea>
                </div>
            </form>
        `;
        
        Modal.show({
            title,
            content,
            width: '600px',
            onConfirm: async () => {
                const form = document.getElementById('pointForm');
                const formData = new FormData(form);
                const data = {
                    point_code: formData.get('point_code'),
                    point_name: formData.get('point_name'),
                    area_id: parseInt(formData.get('area_id')),
                    point_status: formData.get('point_status'),
                    location: formData.get('location'),
                    description: formData.get('description'),
                    monitor_items: this.monitorItems
                };
                
                try {
                    let response;
                    if (id) {
                        response = await EnvMonitorService.updateMonitorPoint(id, data);
                    } else {
                        response = await EnvMonitorService.createMonitorPoint(data);
                    }
                    
                    if (response.code === 200) {
                        Toast.success(response.message);
                        Modal.hide();
                        this.loadStatistics();
                        this.loadMonitorPoints();
                    } else {
                        Toast.error(response.message);
                    }
                } catch (error) {
                    console.error('保存监测点失败:', error);
                    Toast.error('保存失败');
                }
                return false;
            }
        });
    },

    renderMonitorItemsList() {
        if (this.monitorItems.length === 0) {
            return '<p class="text-muted" style="margin: 8px 0;">暂无监测项目</p>';
        }
        
        const presetItems = ['温度', '湿度', 'PM2.5', 'PM10', '噪音', 'CO2', 'CO', '甲醛', 'TVOC', '气压', '风速', '照度'];
        const presetUnits = {
            '温度': '°C', '湿度': '%', 'PM2.5': 'μg/m³', 'PM10': 'μg/m³',
            '噪音': 'dB', 'CO2': 'ppm', 'CO': 'ppm', '甲醛': 'mg/m³',
            'TVOC': 'mg/m³', '气压': 'hPa', '风速': 'm/s', '照度': 'lux'
        };
        
        return `
            <div style="display: grid; gap: 8px;">
                ${this.monitorItems.map((item, idx) => `
                    <div class="form-row" style="gap: 8px; margin-bottom: 0;">
                        <div class="form-group" style="flex: 1;">
                            <select class="form-input" onchange="EnvMonitorPage.updateMonitorItemName(${idx}, this.value)">
                                <option value="">自定义</option>
                                ${presetItems.map(p => `<option value="${p}" ${item.name === p ? 'selected' : ''}>${p}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <input type="text" class="form-input" placeholder="项目名称" 
                                value="${Validator.sanitize(item.name)}" 
                                onchange="EnvMonitorPage.updateMonitorItemName(${idx}, this.value)">
                        </div>
                        <div class="form-group" style="width: 100px;">
                            <input type="text" class="form-input" placeholder="单位" 
                                value="${Validator.sanitize(item.unit || '')}" 
                                onchange="EnvMonitorPage.updateMonitorItemUnit(${idx}, this.value)">
                        </div>
                        <div class="form-group" style="width: 40px;">
                            <button type="button" class="btn btn-sm btn-danger" onclick="EnvMonitorPage.removeMonitorItem(${idx})" style="width: 100%;">×</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    addMonitorItem() {
        this.monitorItems.push({ name: '', unit: '' });
        this.refreshMonitorItemsList();
    },

    updateMonitorItemName(idx, value) {
        const presetUnits = {
            '温度': '°C', '湿度': '%', 'PM2.5': 'μg/m³', 'PM10': 'μg/m³',
            '噪音': 'dB', 'CO2': 'ppm', 'CO': 'ppm', '甲醛': 'mg/m³',
            'TVOC': 'mg/m³', '气压': 'hPa', '风速': 'm/s', '照度': 'lux'
        };
        
        this.monitorItems[idx].name = value;
        if (presetUnits[value] && !this.monitorItems[idx].unit) {
            this.monitorItems[idx].unit = presetUnits[value];
        }
        this.refreshMonitorItemsList();
    },

    updateMonitorItemUnit(idx, value) {
        this.monitorItems[idx].unit = value;
    },

    removeMonitorItem(idx) {
        this.monitorItems.splice(idx, 1);
        this.refreshMonitorItemsList();
    },

    refreshMonitorItemsList() {
        const container = document.getElementById('monitorItemsContainer');
        if (container) {
            container.innerHTML = this.renderMonitorItemsList();
        }
    },

    async deletePoint(id) {
        const confirmed = await Modal.confirm('确定要删除该监测点吗？关联的读数数据也将被删除。');
        if (!confirmed) return;
        
        try {
            const response = await EnvMonitorService.deleteMonitorPoint(id);
            if (response.code === 200) {
                Toast.success(response.message);
                this.loadStatistics();
                this.loadMonitorPoints();
            } else {
                Toast.error(response.message);
            }
        } catch (error) {
            console.error('删除监测点失败:', error);
            Toast.error('删除失败');
        }
    },

    // ==================== 历史趋势 ====================

    async loadHistoryTrend() {
        const container = document.getElementById('tabContent');
        
        // 获取区域列表用于筛选
        let areas = [];
        try {
            const response = await EnvMonitorService.getAreas({ page: 1, size: 100 });
            if (response.code === 200) {
                areas = response.data?.items || [];
            }
        } catch (error) {
            console.error('加载区域列表失败:', error);
        }
        
        if (!this.currentAreaId && areas.length > 0) {
            this.currentAreaId = areas[0].id;
        }
        
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">历史趋势分析</h3>
                </div>
                <div class="card-body">
                    <div class="form-row" style="margin-bottom: 16px;">
                        <div class="form-group">
                            <label>选择区域</label>
                            <select class="form-input" id="historyAreaSelect" onchange="EnvMonitorPage.onAreaChange(this.value)">
                                ${areas.map(a => `<option value="${a.id}" ${this.currentAreaId === a.id ? 'selected' : ''}>${Validator.sanitize(a.area_name)}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>时间窗口</label>
                            <div class="btn-group" id="timeWindowGroup">
                                <button class="btn btn-sm ${this.timeWindow === '1h' ? 'btn-primary' : 'btn-outline'}" onclick="EnvMonitorPage.onTimeWindowChange('1h')">1小时</button>
                                <button class="btn btn-sm ${this.timeWindow === '6h' ? 'btn-primary' : 'btn-outline'}" onclick="EnvMonitorPage.onTimeWindowChange('6h')">6小时</button>
                                <button class="btn btn-sm ${this.timeWindow === '24h' ? 'btn-primary' : 'btn-outline'}" onclick="EnvMonitorPage.onTimeWindowChange('24h')">24小时</button>
                                <button class="btn btn-sm ${this.timeWindow === '7d' ? 'btn-primary' : 'btn-outline'}" onclick="EnvMonitorPage.onTimeWindowChange('7d')">7天</button>
                            </div>
                        </div>
                    </div>
                    <div class="form-group" style="margin-bottom: 16px;">
                        <label>选择监测项目（可多选）</label>
                        <div class="env-item-selector" id="itemSelector">
                            ${this.renderItemSelector()}
                        </div>
                    </div>
                    <div style="height: 400px; background: var(--bg-light); border-radius: 8px; display: flex; align-items: center; justify-content: center;" id="chartContainer">
                        <button class="btn btn-primary" onclick="EnvMonitorPage.loadHistoryData()">📊 查看趋势</button>
                    </div>
                </div>
            </div>
        `;
    },

    renderItemSelector() {
        const presetItems = ['温度', '湿度', 'PM2.5', 'PM10', '噪音', 'CO2', 'CO', '甲醛', 'TVOC'];
        const colors = ['#3366cc', '#dc3912', '#ff9900', '#109618', '#990099', '#0099c6', '#dd4477', '#66aa00', '#b82e2e'];
        
        return presetItems.map((item, idx) => `
            <label class="env-item-checkbox">
                <input type="checkbox" value="${item}" ${this.selectedItems.includes(item) ? 'checked' : ''} 
                    onchange="EnvMonitorPage.onItemToggle('${item}', this.checked)">
                <span class="check-icon" style="background: ${colors[idx]};"></span>
                <span>${item}</span>
            </label>
        `).join('');
    },

    onAreaChange(areaId) {
        this.currentAreaId = parseInt(areaId);
    },

    onTimeWindowChange(window) {
        this.timeWindow = window;
        document.querySelectorAll('#timeWindowGroup .btn').forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline');
        });
        event.target.classList.remove('btn-outline');
        event.target.classList.add('btn-primary');
    },

    onItemToggle(item, checked) {
        if (checked) {
            if (!this.selectedItems.includes(item)) {
                this.selectedItems.push(item);
            }
        } else {
            this.selectedItems = this.selectedItems.filter(i => i !== item);
        }
    },

    async loadHistoryData() {
        if (!this.currentAreaId) {
            Toast.warning('请先选择区域');
            return;
        }
        if (this.selectedItems.length === 0) {
            Toast.warning('请至少选择一个监测项目');
            return;
        }
        
        const container = document.getElementById('chartContainer');
        container.innerHTML = '<div class="loading">加载数据中...</div>';
        
        try {
            const response = await EnvMonitorService.getHistoryTrend({
                areaId: this.currentAreaId,
                itemNames: this.selectedItems.join(','),
                timeWindow: this.timeWindow
            });
            
            if (response.code === 200) {
                this.renderHistoryChart(response.data);
            } else {
                container.innerHTML = `<div class="empty-text">${response.message}</div>`;
            }
        } catch (error) {
            console.error('加载历史数据失败:', error);
            container.innerHTML = '<div class="empty-text">加载数据失败</div>';
        }
    },

    renderHistoryChart(data) {
        const container = document.getElementById('chartContainer');
        container.innerHTML = '<canvas id="historyChart"></canvas>';
        
        const ctx = document.getElementById('historyChart').getContext('2d');
        
        const colors = {
            '温度': '#3366cc', '湿度': '#dc3912', 'PM2.5': '#ff9900', 'PM10': '#109618',
            '噪音': '#990099', 'CO2': '#0099c6', 'CO': '#dd4477', '甲醛': '#66aa00', 'TVOC': '#b82e2e'
        };
        
        const chartData = data.data || {};
        const datasets = [];
        
        for (const itemName of data.item_names || []) {
            const itemData = chartData[itemName] || [];
            datasets.push({
                label: itemName,
                data: itemData.map(d => ({ x: d.time, y: d.value })),
                borderColor: colors[itemName] || '#333',
                backgroundColor: (colors[itemName] || '#333') + '20',
                fill: false,
                tension: 0.3,
                pointRadius: 3,
                pointHoverRadius: 6
            });
        }
        
        if (this.historyChart) {
            this.historyChart.destroy();
        }
        
        this.historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: datasets[0]?.data.map(d => d.x) || [],
                        title: {
                            display: true,
                            text: '时间'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '数值'
                        }
                    }
                }
            }
        });
    },

    // ==================== 阈值配置 ====================

    async loadStandards() {
        const container = document.getElementById('tabContent');
        try {
            const response = await EnvMonitorService.getStandards({ page: 1, size: 100 });
            if (response.code === 200) {
                this.renderStandards(response.data?.items || []);
            }
        } catch (error) {
            console.error('加载阈值配置失败:', error);
            container.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">加载阈值配置失败</div></div>';
        }
    },

    renderStandards(standards) {
        const container = document.getElementById('tabContent');
        
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">环境标准配置</h3>
                    <button class="btn btn-sm btn-primary" onclick="EnvMonitorPage.showStandardModal()">+ 新增标准</button>
                </div>
                <div class="card-body">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>监测项目</th>
                                <th>单位</th>
                                <th>安全下限</th>
                                <th>安全上限</th>
                                <th>告警下限</th>
                                <th>告警上限</th>
                                <th>告警级别</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="standardsTableBody">
                            ${standards.map(s => this.renderStandardRow(s)).join('')}
                        </tbody>
                    </table>
                    ${standards.length === 0 ? '<div class="empty-state"><div class="empty-icon">⚙️</div><div class="empty-text">暂无阈值配置</div></div>' : ''}
                </div>
            </div>
        `;
    },

    renderStandardRow(standard) {
        const severityMap = {
            'info': { text: '提示', class: 'idle' },
            'warning': { text: '警告', class: 'maintenance' },
            'error': { text: '错误', class: 'error' },
            'critical': { text: '严重', class: 'error' }
        };
        const severity = severityMap[standard.severity] || severityMap.warning;
        
        return `
            <tr>
                <td><strong>${Validator.sanitize(standard.item_name)}</strong></td>
                <td>${Validator.sanitize(standard.item_unit || '-')}</td>
                <td>${standard.safety_low !== null ? standard.safety_low : '-'}</td>
                <td>${standard.safety_high !== null ? standard.safety_high : '-'}</td>
                <td><span style="color: var(--warning-color);">${standard.alert_low !== null ? standard.alert_low : '-'}</span></td>
                <td><span style="color: var(--danger-color);">${standard.alert_high !== null ? standard.alert_high : '-'}</span></td>
                <td><span class="status-badge ${severity.class}">${severity.text}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="EnvMonitorPage.showStandardModal(${standard.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="EnvMonitorPage.deleteStandard(${standard.id})">删除</button>
                </td>
            </tr>
        `;
    },

    async showStandardModal(id = null) {
        let standard = null;
        
        if (id) {
            try {
                const response = await EnvMonitorService.getStandard(id);
                if (response.code === 200) {
                    standard = response.data;
                }
            } catch (error) {
                console.error('获取标准数据失败:', error);
            }
        }
        
        const presetItems = [
            { name: '温度', unit: '°C' }, { name: '湿度', unit: '%' },
            { name: 'PM2.5', unit: 'μg/m³' }, { name: 'PM10', unit: 'μg/m³' },
            { name: '噪音', unit: 'dB' }, { name: 'CO2', unit: 'ppm' },
            { name: 'CO', unit: 'ppm' }, { name: '甲醛', unit: 'mg/m³' },
            { name: 'TVOC', unit: 'mg/m³' }, { name: '气压', unit: 'hPa' },
            { name: '风速', unit: 'm/s' }, { name: '照度', unit: 'lux' }
        ];
        
        const title = id ? '编辑标准' : '新增标准';
        const content = `
            <form id="standardForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>监测项目 *</label>
                        <select class="form-input" id="itemNameSelect" onchange="EnvMonitorPage.onStandardItemChange(this.value)">
                            <option value="">自定义</option>
                            ${presetItems.map(p => `<option value="${p.name}" ${standard?.item_name === p.name ? 'selected' : ''}>${p.name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>自定义名称</label>
                        <input type="text" class="form-input" name="item_name" value="${standard?.item_name || ''}" ${id ? 'readonly' : ''}>
                    </div>
                </div>
                <div class="form-group">
                    <label>单位</label>
                    <input type="text" class="form-input" name="item_unit" id="itemUnitInput" value="${standard?.item_unit || ''}">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>安全下限</label>
                        <input type="number" step="0.01" class="form-input" name="safety_low" value="${standard?.safety_low ?? ''}">
                    </div>
                    <div class="form-group">
                        <label>安全上限</label>
                        <input type="number" step="0.01" class="form-input" name="safety_high" value="${standard?.safety_high ?? ''}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label style="color: var(--warning-color);">告警下限</label>
                        <input type="number" step="0.01" class="form-input" name="alert_low" value="${standard?.alert_low ?? ''}">
                    </div>
                    <div class="form-group">
                        <label style="color: var(--danger-color);">告警上限</label>
                        <input type="number" step="0.01" class="form-input" name="alert_high" value="${standard?.alert_high ?? ''}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>告警级别</label>
                        <select class="form-input" name="severity">
                            <option value="info" ${standard?.severity === 'info' ? 'selected' : ''}>提示</option>
                            <option value="warning" ${standard?.severity === 'warning' ? 'selected' : ''}>警告</option>
                            <option value="error" ${standard?.severity === 'error' ? 'selected' : ''}>错误</option>
                            <option value="critical" ${standard?.severity === 'critical' ? 'selected' : ''}>严重</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>标准说明</label>
                    <textarea class="form-input" name="description" rows="2">${standard?.description || ''}</textarea>
                </div>
            </form>
        `;
        
        Modal.show({
            title,
            content,
            width: '500px',
            onConfirm: async () => {
                const form = document.getElementById('standardForm');
                const formData = new FormData(form);
                
                const itemNameSelect = document.getElementById('itemNameSelect');
                const selectedName = itemNameSelect.value || formData.get('item_name');
                
                if (!selectedName) {
                    Toast.warning('请输入或选择监测项目');
                    return false;
                }
                
                const data = {
                    item_name: selectedName,
                    item_unit: formData.get('item_unit'),
                    safety_low: formData.get('safety_low') ? parseFloat(formData.get('safety_low')) : null,
                    safety_high: formData.get('safety_high') ? parseFloat(formData.get('safety_high')) : null,
                    alert_low: formData.get('alert_low') ? parseFloat(formData.get('alert_low')) : null,
                    alert_high: formData.get('alert_high') ? parseFloat(formData.get('alert_high')) : null,
                    severity: formData.get('severity'),
                    description: formData.get('description')
                };
                
                try {
                    let response;
                    if (id) {
                        response = await EnvMonitorService.updateStandard(id, data);
                    } else {
                        response = await EnvMonitorService.createStandard(data);
                    }
                    
                    if (response.code === 200) {
                        Toast.success(response.message);
                        Modal.hide();
                        this.loadStandards();
                    } else {
                        Toast.error(response.message);
                    }
                } catch (error) {
                    console.error('保存标准失败:', error);
                    Toast.error('保存失败');
                }
                return false;
            }
        });
    },

    onStandardItemChange(value) {
        const presetUnits = {
            '温度': '°C', '湿度': '%', 'PM2.5': 'μg/m³', 'PM10': 'μg/m³',
            '噪音': 'dB', 'CO2': 'ppm', 'CO': 'ppm', '甲醛': 'mg/m³',
            'TVOC': 'mg/m³', '气压': 'hPa', '风速': 'm/s', '照度': 'lux'
        };
        
        const nameInput = document.querySelector('input[name="item_name"]');
        const unitInput = document.getElementById('itemUnitInput');
        
        if (value) {
            nameInput.value = value;
            if (presetUnits[value]) {
                unitInput.value = presetUnits[value];
            }
        }
    },

    async deleteStandard(id) {
        const confirmed = await Modal.confirm('确定要删除该标准吗？');
        if (!confirmed) return;
        
        try {
            const response = await EnvMonitorService.deleteStandard(id);
            if (response.code === 200) {
                Toast.success(response.message);
                this.loadStandards();
            } else {
                Toast.error(response.message);
            }
        } catch (error) {
            console.error('删除标准失败:', error);
            Toast.error('删除失败');
        }
    },

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        if (this.historyChart) {
            this.historyChart.destroy();
            this.historyChart = null;
        }
    }
};

// 全局可用
window.EnvMonitorPage = EnvMonitorPage;
