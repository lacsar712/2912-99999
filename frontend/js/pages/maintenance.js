/**
 * 维修工单页面
 */
const MaintenancePage = {
    workOrders: [],
    equipments: [],
    parts: [],
    currentOrder: null,
    viewMode: 'list',

    init() {
        this.render();
        this.loadData();
    },

    render() {
        const container = document.getElementById('pageContainer');
        if (this.viewMode === 'detail') {
            this.renderDetail(container);
        } else {
            this.renderList(container);
        }
    },

    async loadData() {
        try {
            const [ordersRes, equipRes, partsRes] = await Promise.all([
                MaintenanceService.getWorkOrders({ size: 1000 }),
                ProductionService.getEquipments({ size: 1000 }),
                SpareService.getParts({ size: 1000 })
            ]);

            if (ordersRes.code === 200) this.workOrders = ordersRes.data?.items || [];
            if (equipRes.code === 200) this.equipments = equipRes.data?.items || [];
            if (partsRes.code === 200) this.parts = partsRes.data?.items || [];

            if (this.viewMode === 'list') {
                this.renderOrderTable();
            } else if (this.currentOrder) {
                this.loadOrderDetail(this.currentOrder.id);
            }
        } catch (error) {
            Toast.error('加载数据失败');
        }
    },

    renderList(container) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 class="card-title">维修工单</h3>
                    <div id="orderStats" style="display: flex; gap: 16px; font-size: 13px;">
                    </div>
                </div>
                <div class="card-body">
                    <div class="toolbar">
                        <div class="toolbar-left">
                            <select class="form-control" id="statusFilter" style="width: 120px;">
                                <option value="">全部状态</option>
                                <option value="pending">待处理</option>
                                <option value="in_progress">处理中</option>
                                <option value="completed">已完成</option>
                                <option value="cancelled">已取消</option>
                            </select>
                            <select class="form-control" id="priorityFilter" style="width: 120px; margin-left: 8px;">
                                <option value="">全部优先级</option>
                                <option value="low">低</option>
                                <option value="medium">中</option>
                                <option value="high">高</option>
                                <option value="critical">紧急</option>
                            </select>
                        </div>
                        <div class="toolbar-right">
                            <button class="btn btn-primary" onclick="MaintenancePage.showOrderModal()">
                                + 新建工单
                            </button>
                        </div>
                    </div>
                    <div id="orderTable"></div>
                </div>
            </div>
        `;

        document.getElementById('statusFilter')?.addEventListener('change', () => this.filterOrders());
        document.getElementById('priorityFilter')?.addEventListener('change', () => this.filterOrders());
        this.renderOrderStats();
    },

    renderOrderStats() {
        const stats = {
            total: this.workOrders.length,
            pending: this.workOrders.filter(o => o.status === 'pending').length,
            in_progress: this.workOrders.filter(o => o.status === 'in_progress').length,
            completed: this.workOrders.filter(o => o.status === 'completed').length
        };

        const el = document.getElementById('orderStats');
        if (!el) return;
        el.innerHTML = `
            <div style="padding: 8px 16px; background: var(--bg-light); border-radius: 6px;">
                <span style="color: var(--text-secondary);">总数:</span>
                <strong style="margin-left: 6px;">${stats.total}</strong>
            </div>
            <div style="padding: 8px 16px; background: #fff3cd; border-radius: 6px;">
                <span style="color: var(--text-secondary);">待处理:</span>
                <strong style="margin-left: 6px; color: #856404;">${stats.pending}</strong>
            </div>
            <div style="padding: 8px 16px; background: #cce5ff; border-radius: 6px;">
                <span style="color: var(--text-secondary);">处理中:</span>
                <strong style="margin-left: 6px; color: #004085;">${stats.in_progress}</strong>
            </div>
            <div style="padding: 8px 16px; background: #d4edda; border-radius: 6px;">
                <span style="color: var(--text-secondary);">已完成:</span>
                <strong style="margin-left: 6px; color: #155724;">${stats.completed}</strong>
            </div>
        `;
    },

    renderOrderTable(data = this.workOrders) {
        const container = document.getElementById('orderTable');
        if (!container) return;

        new DataTable('#orderTable', {
            columns: [
                { field: 'order_code', title: '工单编号' },
                { field: 'order_name', title: '工单名称' },
                { field: 'equipment_name', title: '设备', render: (v, row) => v || row.equipment_id },
                { 
                    field: 'priority', 
                    title: '优先级',
                    render: (v) => {
                        const colors = { low: 'badge-success', medium: 'badge-warning', high: 'badge-danger', critical: 'badge-danger' };
                        const texts = { low: '低', medium: '中', high: '高', critical: '紧急' };
                        return `<span class="badge ${colors[v]}">${texts[v]}</span>`;
                    }
                },
                { 
                    field: 'status', 
                    title: '状态', 
                    render: (v) => {
                        const map = { 
                            pending: { text: '待处理', class: 'badge-warning' }, 
                            in_progress: { text: '处理中', class: 'badge-primary' }, 
                            completed: { text: '已完成', class: 'badge-success' },
                            cancelled: { text: '已取消', class: 'badge-secondary' }
                        };
                        return `<span class="badge ${map[v]?.class}">${map[v]?.text}</span>`;
                    }
                },
                { field: 'assigned_to', title: '负责人', render: (v) => v || '-' },
                { field: 'materials_cost', title: '耗材费用', render: (v) => v ? `¥${v.toFixed(2)}` : '-' },
                { field: 'total_cost', title: '总费用', render: (v) => v ? `¥${v.toFixed(2)}` : '-' },
                { field: 'create_time', title: '创建时间' },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id, row) => `
                        <button class="btn btn-sm btn-outline" onclick="MaintenancePage.viewDetail(${id})">详情</button>
                        <button class="btn btn-sm btn-outline" onclick="MaintenancePage.showOrderModal(${id})" style="margin-left: 4px;">编辑</button>
                        ${row.status === 'pending' ? `<button class="btn btn-sm btn-success" onclick="MaintenancePage.updateStatus(${id}, 'in_progress')" style="margin-left: 4px;">开始</button>` : ''}
                        ${row.status === 'in_progress' ? `<button class="btn btn-sm btn-success" onclick="MaintenancePage.updateStatus(${id}, 'completed')" style="margin-left: 4px;">完成</button>` : ''}
                    `
                }
            ],
            data: data
        });
    },

    filterOrders() {
        const status = document.getElementById('statusFilter')?.value;
        const priority = document.getElementById('priorityFilter')?.value;

        let filtered = [...this.workOrders];
        if (status) filtered = filtered.filter(o => o.status === status);
        if (priority) filtered = filtered.filter(o => o.priority === priority);

        this.renderOrderTable(filtered);
    },

    async viewDetail(id) {
        this.currentOrder = this.workOrders.find(o => o.id === id);
        this.viewMode = 'detail';
        this.render();
        await this.loadOrderDetail(id);
    },

    backToList() {
        this.currentOrder = null;
        this.viewMode = 'list';
        this.render();
        this.renderOrderTable();
    },

    async loadOrderDetail(id) {
        try {
            const res = await MaintenanceService.getWorkOrderById(id);
            if (res.code === 200) {
                this.currentOrder = res.data;
                this.renderDetailContent();
            }
        } catch (error) {
            Toast.error('加载工单详情失败');
        }
    },

    renderDetail(container) {
        if (!this.currentOrder) {
            this.backToList();
            return;
        }

        container.innerHTML = `
            <div class="card">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <button class="btn btn-outline btn-sm" onclick="MaintenancePage.backToList()">← 返回列表</button>
                        <h3 class="card-title" style="margin: 0;">工单详情 - ${this.currentOrder.order_code}</h3>
                    </div>
                    <div>
                        ${this.renderStatusBadge(this.currentOrder.status)}
                    </div>
                </div>
                <div class="card-body" id="detailContent">
                    <div class="loading-container" style="text-align: center; padding: 40px;">
                        <div class="loading-spinner"></div>
                        <div style="margin-top: 10px; color: var(--text-secondary);">加载中...</div>
                    </div>
                </div>
            </div>
        `;
    },

    renderStatusBadge(status) {
        const map = { 
            pending: { text: '待处理', class: 'badge-warning' }, 
            in_progress: { text: '处理中', class: 'badge-primary' }, 
            completed: { text: '已完成', class: 'badge-success' },
            cancelled: { text: '已取消', class: 'badge-secondary' }
        };
        return `<span class="badge ${map[status]?.class}" style="font-size: 14px; padding: 6px 12px;">${map[status]?.text}</span>`;
    },

    renderDetailContent() {
        const container = document.getElementById('detailContent');
        if (!container || !this.currentOrder) return;

        const order = this.currentOrder;
        let materials = [];
        try {
            materials = order.materials ? JSON.parse(order.materials) : [];
        } catch (e) {
            materials = [];
        }

        container.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div class="card" style="margin: 0;">
                    <div class="card-header" style="padding: 12px 16px;">
                        <h4 style="margin: 0; font-size: 16px;">基本信息</h4>
                    </div>
                    <div class="card-body" style="padding: 16px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary); width: 100px;">工单名称</td>
                                <td style="padding: 8px 0; font-weight: 500;">${order.order_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">工单编号</td>
                                <td style="padding: 8px 0;">${order.order_code}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">关联设备</td>
                                <td style="padding: 8px 0;">${order.equipment_name || order.equipment_id || '-'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">设备类型</td>
                                <td style="padding: 8px 0;">${order.equipment_type || '-'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">优先级</td>
                                <td style="padding: 8px 0;">${this.getPriorityText(order.priority)}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">负责人</td>
                                <td style="padding: 8px 0;">${order.assigned_to || '-'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">计划时间</td>
                                <td style="padding: 8px 0;">${order.plan_start_time || '-'} ~ ${order.plan_end_time || '-'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">实际时间</td>
                                <td style="padding: 8px 0;">${order.actual_start_time || '-'} ~ ${order.actual_end_time || '-'}</td>
                            </tr>
                        </table>
                    </div>
                </div>

                <div class="card" style="margin: 0;">
                    <div class="card-header" style="padding: 12px 16px;">
                        <h4 style="margin: 0; font-size: 16px;">费用信息</h4>
                    </div>
                    <div class="card-body" style="padding: 16px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary); width: 100px;">耗材费用</td>
                                <td style="padding: 8px 0; font-weight: 500; color: #dc3545;">¥${(order.materials_cost || 0).toFixed(2)}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">人工费用</td>
                                <td style="padding: 8px 0; font-weight: 500;">¥${(order.labor_cost || 0).toFixed(2)}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: var(--text-secondary);">总费用</td>
                                <td style="padding: 8px 0; font-weight: bold; font-size: 18px; color: #dc3545;">¥${(order.total_cost || 0).toFixed(2)}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>

            <div class="card" style="margin-bottom: 20px;">
                <div class="card-header" style="padding: 12px 16px;">
                    <h4 style="margin: 0; font-size: 16px;">故障描述</h4>
                </div>
                <div class="card-body" style="padding: 16px;">
                    ${order.fault_description || '暂无'}
                </div>
            </div>

            <div class="card" style="margin-bottom: 20px;">
                <div class="card-header" style="padding: 12px 16px;">
                    <h4 style="margin: 0; font-size: 16px;">维修内容</h4>
                </div>
                <div class="card-body" style="padding: 16px;">
                    ${order.work_content || '暂无'}
                </div>
            </div>

            <div class="card">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px;">
                    <h4 style="margin: 0; font-size: 16px;">📦 领用备件</h4>
                    ${order.status !== 'completed' && order.status !== 'cancelled' ? 
                        `<button class="btn btn-primary btn-sm" onclick="MaintenancePage.showUseSpareModal()">+ 领用备件</button>` : ''}
                </div>
                <div class="card-body" style="padding: 0;">
                    <div id="spareUsageSection" style="padding: 16px;">
                    </div>
                </div>
            </div>
        `;

        this.renderSpareUsageSection();
    },

    renderSpareUsageSection() {
        const container = document.getElementById('spareUsageSection');
        if (!container || !this.currentOrder) return;

        const spareUsage = this.currentOrder.spare_usage || [];
        let materials = [];
        try {
            materials = this.currentOrder.materials ? JSON.parse(this.currentOrder.materials) : [];
        } catch (e) {
            materials = [];
        }

        if (spareUsage.length === 0 && materials.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    暂无领用记录
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 2px solid var(--border-color);">
                        <th style="text-align: left; padding: 12px 8px; font-weight: 600;">备件编号</th>
                        <th style="text-align: left; padding: 12px 8px; font-weight: 600;">备件名称</th>
                        <th style="text-align: left; padding: 12px 8px; font-weight: 600;">规格</th>
                        <th style="text-align: left; padding: 12px 8px; font-weight: 600;">单位</th>
                        <th style="text-align: right; padding: 12px 8px; font-weight: 600;">数量</th>
                        <th style="text-align: right; padding: 12px 8px; font-weight: 600;">单价</th>
                        <th style="text-align: right; padding: 12px 8px; font-weight: 600;">总价</th>
                        <th style="text-align: left; padding: 12px 8px; font-weight: 600;">领用人</th>
                        <th style="text-align: left; padding: 12px 8px; font-weight: 600;">领用时间</th>
                        <th style="text-align: left; padding: 12px 8px; font-weight: 600;">状态</th>
                    </tr>
                </thead>
                <tbody>
                    ${spareUsage.map(item => `
                        <tr style="border-bottom: 1px solid var(--border-light);">
                            <td style="padding: 12px 8px;">${item.part_code}</td>
                            <td style="padding: 12px 8px;">${item.part_name}</td>
                            <td style="padding: 12px 8px;">${item.specification || '-'}</td>
                            <td style="padding: 12px 8px;">${item.unit}</td>
                            <td style="padding: 12px 8px; text-align: right;">${item.quantity}</td>
                            <td style="padding: 12px 8px; text-align: right;">¥${(item.unit_price || 0).toFixed(2)}</td>
                            <td style="padding: 12px 8px; text-align: right;">¥${(item.total_price || 0).toFixed(2)}</td>
                            <td style="padding: 12px 8px;">${item.receiver}</td>
                            <td style="padding: 12px 8px;">${item.outbound_time}</td>
                            <td style="padding: 12px 8px;">
                                ${item.is_returned === 1 ? 
                                    '<span class="badge badge-success">已归还</span>' : 
                                    (this.currentOrder.status !== 'completed' && this.currentOrder.status !== 'cancelled' ? 
                                        `<button class="btn btn-sm btn-success" onclick="MaintenancePage.returnSpare(${item.id})">归还</button>` :
                                        '<span class="badge badge-warning">未归还</span>'
                                    )
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },

    getPriorityText(priority) {
        const map = { low: '低', medium: '中', high: '高', critical: '紧急' };
        const colors = { low: 'text-success', medium: 'text-warning', high: 'text-danger', critical: 'text-danger' };
        return `<span class="${colors[priority]}">${map[priority]}</span>`;
    },

    async showOrderModal(id = null) {
        const order = id ? this.workOrders.find(o => o.id === id) : null;
        const isEdit = !!order;

        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">${isEdit ? '编辑' : '新建'}工单</h4>
                <form id="orderForm">
                    <div class="form-group">
                        <label>工单名称 *</label>
                        <input type="text" class="form-control" name="order_name" value="${order?.order_name || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>关联设备 *</label>
                        <select class="form-control" name="equipment_id" required>
                            <option value="">请选择设备</option>
                            ${this.equipments.map(e => `<option value="${e.id}" ${order?.equipment_id === e.id ? 'selected' : ''}>${e.equipment_code} - ${e.equipment_name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>故障描述</label>
                        <textarea class="form-control" name="fault_description" rows="3">${order?.fault_description || ''}</textarea>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>维修类型</label>
                            <select class="form-control" name="work_type">
                                <option value="corrective" ${order?.work_type === 'corrective' ? 'selected' : ''}>故障维修</option>
                                <option value="predictive" ${order?.work_type === 'predictive' ? 'selected' : ''}>预测维修</option>
                                <option value="preventive" ${order?.work_type === 'preventive' ? 'selected' : ''}>预防维修</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>优先级</label>
                            <select class="form-control" name="priority">
                                <option value="low" ${order?.priority === 'low' ? 'selected' : ''}>低</option>
                                <option value="medium" ${order?.priority === 'medium' ? 'selected' : ''}>中</option>
                                <option value="high" ${order?.priority === 'high' ? 'selected' : ''}>高</option>
                                <option value="critical" ${order?.priority === 'critical' ? 'selected' : ''}>紧急</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>计划开始时间</label>
                            <input type="datetime-local" class="form-control" name="plan_start_time" value="${order?.plan_start_time ? order.plan_start_time.slice(0, 16) : ''}">
                        </div>
                        <div class="form-group">
                            <label>计划结束时间</label>
                            <input type="datetime-local" class="form-control" name="plan_end_time" value="${order?.plan_end_time ? order.plan_end_time.slice(0, 16) : ''}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>负责人</label>
                        <input type="text" class="form-control" name="assigned_to" value="${order?.assigned_to || ''}">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>人工费用 (元)</label>
                            <input type="number" class="form-control" name="labor_cost" value="${order?.labor_cost || 0}" min="0" step="0.01">
                        </div>
                        <div class="form-group">
                            <label>状态</label>
                            <select class="form-control" name="status">
                                <option value="pending" ${order?.status === 'pending' ? 'selected' : ''}>待处理</option>
                                <option value="in_progress" ${order?.status === 'in_progress' ? 'selected' : ''}>处理中</option>
                                <option value="completed" ${order?.status === 'completed' ? 'selected' : ''}>已完成</option>
                                <option value="cancelled" ${order?.status === 'cancelled' ? 'selected' : ''}>已取消</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>维修内容</label>
                        <textarea class="form-control" name="work_content" rows="3">${order?.work_content || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea class="form-control" name="remark" rows="2">${order?.remark || ''}</textarea>
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: isEdit ? '编辑工单' : '新建工单',
            content: html,
            width: 600,
            onConfirm: async () => {
                const form = document.getElementById('orderForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (key === 'equipment_id') {
                        data[key] = value ? parseInt(value) : null;
                    } else if (key === 'labor_cost') {
                        data[key] = parseFloat(value) || 0;
                    } else {
                        data[key] = value;
                    }
                });

                try {
                    let res;
                    if (isEdit) {
                        res = await MaintenanceService.updateWorkOrder(id, data);
                    } else {
                        res = await MaintenanceService.createWorkOrder(data);
                    }
                    if (res.code === 200 || res.code === 201) {
                        Toast.success(isEdit ? '更新成功' : '创建成功');
                        Modal.close();
                        this.loadData();
                    } else {
                        Toast.error(res.message);
                    }
                } catch (error) {
                    Toast.error('操作失败');
                }
            }
        });
    },

    async updateStatus(id, status) {
        const confirmed = await Modal.confirm(`确定要将工单状态更新为"${status === 'in_progress' ? '处理中' : '已完成'}"吗？`);
        if (!confirmed) return;
        try {
            const res = await MaintenanceService.updateWorkOrderStatus(id, status);
            if (res.code === 200) {
                Toast.success('状态更新成功');
                this.loadData();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    },

    async showUseSpareModal() {
        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">领用备件</h4>
                <form id="useSpareForm">
                    <div class="form-group">
                        <label>选择备件 *</label>
                        <select class="form-control" name="spare_part_id" required onchange="SpareService.getPartById(this.value).then(r => { if(r.code===200){document.getElementById('useStockInfo').textContent='当前库存: '+r.data.current_stock} })">
                            <option value="">请选择备件</option>
                            ${this.parts.filter(p => p.current_stock > 0).map(p => `<option value="${p.id}">${p.part_code} - ${p.part_name} (库存: ${p.current_stock})</option>`).join('')}
                        </select>
                        <small id="useStockInfo" style="color: var(--text-secondary); margin-top: 4px; display: block;"></small>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>领用数量 *</label>
                            <input type="number" class="form-control" name="quantity" min="1" required>
                        </div>
                        <div class="form-group">
                            <label>领用人 *</label>
                            <input type="text" class="form-control" name="receiver" value="${AuthService.getCurrentUser()?.username || ''}" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea class="form-control" name="remark" rows="2"></textarea>
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: '领用备件',
            content: html,
            width: 500,
            onConfirm: async () => {
                const form = document.getElementById('useSpareForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (['spare_part_id', 'quantity'].includes(key)) {
                        data[key] = parseInt(value);
                    } else {
                        data[key] = value;
                    }
                });
                data.work_order_id = this.currentOrder.id;
                data.reason = `维修工单 ${this.currentOrder.order_code} 领用`;
                data.operator = AuthService.getCurrentUser()?.username || '';

                try {
                    const res = await SpareService.createOutbound(data);
                    if (res.code === 201) {
                        Toast.success('领用成功');
                        Modal.close();
                        this.loadOrderDetail(this.currentOrder.id);
                    } else {
                        Toast.error(res.message);
                    }
                } catch (error) {
                    Toast.error('操作失败');
                }
            }
        });
    },

    async returnSpare(outboundId) {
        const confirmed = await Modal.confirm('确定要归还该备件吗？');
        if (!confirmed) return;
        try {
            const res = await SpareService.returnOutbound(outboundId);
            if (res.code === 200) {
                Toast.success('归还成功');
                this.loadOrderDetail(this.currentOrder.id);
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    },

    destroy() {
    }
};

window.MaintenancePage = MaintenancePage;
