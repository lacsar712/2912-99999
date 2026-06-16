/**
 * 备件管理页面
 */
const SparePage = {
    currentTab: 'parts',
    parts: [],
    equipmentTypes: [],
    equipments: [],
    workOrders: [],
    inbounds: [],
    outbounds: [],
    inventories: [],
    turnoverRates: [],
    dashboard: null,

    init() {
        this.render();
        this.loadData();
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 class="card-title">备件管理</h3>
                    <div id="dashboardSummary" style="display: flex; gap: 16px; font-size: 13px;">
                    </div>
                </div>
                <div class="card-body">
                    <div class="safety-tab-bar" style="margin-bottom: 20px;">
                        <div class="safety-tab active" data-tab="parts" onclick="SparePage.switchTab('parts')">
                            📋 备件档案
                        </div>
                        <div class="safety-tab" data-tab="inbound" onclick="SparePage.switchTab('inbound')">
                            📥 入库管理
                        </div>
                        <div class="safety-tab" data-tab="outbound" onclick="SparePage.switchTab('outbound')">
                            📤 领用管理
                        </div>
                        <div class="safety-tab" data-tab="inventory" onclick="SparePage.switchTab('inventory')">
                            📊 月度盘点
                        </div>
                        <div class="safety-tab" data-tab="turnover" onclick="SparePage.switchTab('turnover')">
                            📈 周转率排行
                        </div>
                    </div>
                    <div id="tabContent"></div>
                </div>
            </div>
        `;
    },

    async loadData() {
        try {
            const [typesRes, equipRes, ordersRes, dashboardRes] = await Promise.all([
                SpareService.getEquipmentTypes(),
                ProductionService.getEquipments({ size: 1000 }),
                MaintenanceService.getWorkOrders({ size: 1000 }),
                SpareService.getDashboard()
            ]);

            if (typesRes.code === 200) this.equipmentTypes = typesRes.data || [];
            if (equipRes.code === 200) this.equipments = equipRes.data?.items || [];
            if (ordersRes.code === 200) this.workOrders = ordersRes.data?.items || [];
            if (dashboardRes.code === 200) this.dashboard = dashboardRes.data;

            this.renderDashboard();
            this.switchTab(this.currentTab);
        } catch (error) {
            Toast.error('加载数据失败');
        }
    },

    renderDashboard() {
        if (!this.dashboard) return;
        const el = document.getElementById('dashboardSummary');
        if (!el) return;
        el.innerHTML = `
            <div style="padding: 8px 16px; background: var(--bg-light); border-radius: 6px;">
                <span style="color: var(--text-secondary);">备件总数:</span>
                <strong style="margin-left: 6px;">${this.dashboard.total_parts}</strong>
            </div>
            <div style="padding: 8px 16px; background: ${this.dashboard.low_stock_parts > 0 ? '#fff3cd' : 'var(--bg-light)'}; border-radius: 6px;">
                <span style="color: var(--text-secondary);">低库存:</span>
                <strong style="margin-left: 6px; color: ${this.dashboard.low_stock_parts > 0 ? '#dc3545' : 'inherit'};">${this.dashboard.low_stock_parts}</strong>
            </div>
            <div style="padding: 8px 16px; background: var(--bg-light); border-radius: 6px;">
                <span style="color: var(--text-secondary);">本月入库:</span>
                <strong style="margin-left: 6px;">${this.dashboard.this_month_inbound}</strong>
            </div>
            <div style="padding: 8px 16px; background: var(--bg-light); border-radius: 6px;">
                <span style="color: var(--text-secondary);">本月出库:</span>
                <strong style="margin-left: 6px;">${this.dashboard.this_month_outbound}</strong>
            </div>
            <div style="padding: 8px 16px; background: var(--bg-light); border-radius: 6px;">
                <span style="color: var(--text-secondary);">库存价值:</span>
                <strong style="margin-left: 6px;">¥${this.dashboard.total_inventory_value?.toFixed(2) || 0}</strong>
            </div>
        `;
    },

    switchTab(tab) {
        this.currentTab = tab;
        document.querySelectorAll('.safety-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });
        const content = document.getElementById('tabContent');
        if (!content) return;

        switch (tab) {
            case 'parts':
                this.renderPartsTab(content);
                this.loadParts();
                break;
            case 'inbound':
                this.renderInboundTab(content);
                this.loadInbounds();
                break;
            case 'outbound':
                this.renderOutboundTab(content);
                this.loadOutbounds();
                break;
            case 'inventory':
                this.renderInventoryTab(content);
                this.loadInventories();
                break;
            case 'turnover':
                this.renderTurnoverTab(content);
                this.loadTurnoverRates();
                break;
        }
    },

    renderPartsTab(container) {
        container.innerHTML = `
            <div class="toolbar">
                <div class="toolbar-left">
                    <select class="form-control" id="eqTypeFilter" style="width: 150px;">
                        <option value="">全部设备类型</option>
                        ${this.equipmentTypes.map(t => `<option value="${t}">${t}</option>`).join('')}
                    </select>
                    <label style="margin-left: 12px; display: flex; align-items: center;">
                        <input type="checkbox" id="lowStockFilter" style="margin-right: 6px;">
                        仅显示低库存
                    </label>
                    <input type="text" class="form-control" id="partSearch" 
                           placeholder="搜索备件编号或名称..." 
                           style="width: 200px; margin-left: 12px;">
                </div>
                <div class="toolbar-right">
                    <button class="btn btn-outline" onclick="SparePage.checkLowStock()">检查低库存</button>
                    <button class="btn btn-primary" onclick="SparePage.showPartModal()" style="margin-left: 8px;">
                        + 新增备件
                    </button>
                </div>
            </div>
            <div id="partsTable"></div>
        `;

        document.getElementById('eqTypeFilter')?.addEventListener('change', () => this.filterParts());
        document.getElementById('lowStockFilter')?.addEventListener('change', () => this.filterParts());
        document.getElementById('partSearch')?.addEventListener('input', () => this.filterParts());
    },

    async loadParts() {
        try {
            const res = await SpareService.getParts({ size: 1000 });
            if (res.code === 200) {
                this.parts = res.data?.items || [];
                this.renderPartsTable();
            }
        } catch (error) {
            Toast.error('加载备件列表失败');
        }
    },

    filterParts() {
        const eqType = document.getElementById('eqTypeFilter')?.value || '';
        const lowStockOnly = document.getElementById('lowStockFilter')?.checked;
        const keyword = document.getElementById('partSearch')?.value?.toLowerCase() || '';

        let filtered = [...this.parts];
        if (eqType) filtered = filtered.filter(p => p.equipment_type === eqType);
        if (lowStockOnly) filtered = filtered.filter(p => p.current_stock <= p.safety_stock);
        if (keyword) {
            filtered = filtered.filter(p => 
                p.part_code?.toLowerCase().includes(keyword) ||
                p.part_name?.toLowerCase().includes(keyword)
            );
        }

        this.renderPartsTable(filtered);
    },

    renderPartsTable(data = this.parts) {
        const container = document.getElementById('partsTable');
        if (!container) return;

        new DataTable('#partsTable', {
            columns: [
                { field: 'part_code', title: '备件编号' },
                { field: 'part_name', title: '备件名称' },
                { field: 'specification', title: '规格', render: (v) => v || '-' },
                { field: 'unit', title: '单位' },
                { field: 'safety_stock', title: '安全库存' },
                { 
                    field: 'current_stock', 
                    title: '当前库存',
                    render: (v, row) => {
                        const isLow = v <= row.safety_stock;
                        return `<span style="color: ${isLow ? '#dc3545' : 'inherit'}; font-weight: ${isLow ? 'bold' : 'normal'};">${v}</span>`;
                    }
                },
                { field: 'equipment_type', title: '设备类型', render: (v) => v || '-' },
                { field: 'unit_price', title: '单价', render: (v) => `¥${v?.toFixed(2) || 0}` },
                { field: 'location', title: '库位', render: (v) => v || '-' },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id, row) => `
                        <button class="btn btn-sm btn-outline" onclick="SparePage.showPartModal(${id})">编辑</button>
                        <button class="btn btn-sm btn-danger" onclick="SparePage.deletePart(${id})" style="margin-left: 4px;">删除</button>
                    `
                }
            ],
            data: data
        });
    },

    async showPartModal(id = null) {
        const part = id ? this.parts.find(p => p.id === id) : null;
        const isEdit = !!part;

        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">${isEdit ? '编辑' : '新增'}备件</h4>
                <form id="partForm">
                    <div class="form-group">
                        <label>备件编号 *</label>
                        <input type="text" class="form-control" name="part_code" value="${part?.part_code || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>备件名称 *</label>
                        <input type="text" class="form-control" name="part_name" value="${part?.part_name || ''}" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>规格</label>
                            <input type="text" class="form-control" name="specification" value="${part?.specification || ''}">
                        </div>
                        <div class="form-group">
                            <label>单位</label>
                            <input type="text" class="form-control" name="unit" value="${part?.unit || ''}">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>安全库存</label>
                            <input type="number" class="form-control" name="safety_stock" value="${part?.safety_stock || 0}" min="0">
                        </div>
                        <div class="form-group">
                            <label>当前库存</label>
                            <input type="number" class="form-control" name="current_stock" value="${part?.current_stock || 0}" min="0">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>设备类型</label>
                            <select class="form-control" name="equipment_type">
                                <option value="">请选择</option>
                                ${this.equipmentTypes.map(t => `<option value="${t}" ${part?.equipment_type === t ? 'selected' : ''}>${t}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>关联设备</label>
                            <select class="form-control" name="equipment_id">
                                <option value="">请选择</option>
                                ${this.equipments.map(e => `<option value="${e.id}" ${part?.equipment_id === e.id ? 'selected' : ''}>${e.equipment_name}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>单价 (元)</label>
                            <input type="number" class="form-control" name="unit_price" value="${part?.unit_price || 0}" min="0" step="0.01">
                        </div>
                        <div class="form-group">
                            <label>库位</label>
                            <input type="text" class="form-control" name="location" value="${part?.location || ''}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea class="form-control" name="remark" rows="2">${part?.remark || ''}</textarea>
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: isEdit ? '编辑备件' : '新增备件',
            content: html,
            width: 600,
            onConfirm: async () => {
                const form = document.getElementById('partForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (key === 'equipment_id') {
                        data[key] = value ? parseInt(value) : null;
                    } else if (['safety_stock', 'current_stock'].includes(key)) {
                        data[key] = parseInt(value) || 0;
                    } else if (key === 'unit_price') {
                        data[key] = parseFloat(value) || 0;
                    } else {
                        data[key] = value;
                    }
                });

                try {
                    let res;
                    if (isEdit) {
                        res = await SpareService.updatePart(id, data);
                    } else {
                        res = await SpareService.createPart(data);
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

    async deletePart(id) {
        const confirmed = await Modal.confirm('确定要删除该备件吗？');
        if (!confirmed) return;
        try {
            const res = await SpareService.deletePart(id);
            if (res.code === 200) {
                Toast.success('删除成功');
                this.loadData();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('删除失败');
        }
    },

    async checkLowStock() {
        try {
            const res = await SpareService.checkLowStock();
            if (res.code === 200) {
                Toast.success(`检查完成，发现 ${res.data?.low_stock_count || 0} 个低库存备件，已生成告警`);
                this.loadData();
            }
        } catch (error) {
            Toast.error('检查失败');
        }
    },

    renderInboundTab(container) {
        container.innerHTML = `
            <div class="toolbar">
                <div class="toolbar-left">
                    <select class="form-control" id="inboundPartFilter" style="width: 180px;">
                        <option value="">全部备件</option>
                        ${this.parts.map(p => `<option value="${p.id}">${p.part_name}</option>`).join('')}
                    </select>
                    <select class="form-control" id="inboundSourceFilter" style="width: 120px; margin-left: 8px;">
                        <option value="">全部来源</option>
                        <option value="purchase">采购入库</option>
                        <option value="return">退库</option>
                    </select>
                </div>
                <div class="toolbar-right">
                    <button class="btn btn-primary" onclick="SparePage.showInboundModal()">
                        + 新增入库
                    </button>
                </div>
            </div>
            <div id="inboundTable"></div>
        `;

        document.getElementById('inboundPartFilter')?.addEventListener('change', () => this.filterInbounds());
        document.getElementById('inboundSourceFilter')?.addEventListener('change', () => this.filterInbounds());
    },

    async loadInbounds() {
        try {
            const res = await SpareService.getInbounds({ size: 1000 });
            if (res.code === 200) {
                this.inbounds = res.data?.items || [];
                this.renderInboundTable();
            }
        } catch (error) {
            Toast.error('加载入库列表失败');
        }
    },

    filterInbounds() {
        const partId = document.getElementById('inboundPartFilter')?.value;
        const sourceType = document.getElementById('inboundSourceFilter')?.value;

        let filtered = [...this.inbounds];
        if (partId) filtered = filtered.filter(i => i.spare_part_id === parseInt(partId));
        if (sourceType) filtered = filtered.filter(i => i.source_type === sourceType);

        this.renderInboundTable(filtered);
    },

    renderInboundTable(data = this.inbounds) {
        const container = document.getElementById('inboundTable');
        if (!container) return;

        new DataTable('#inboundTable', {
            columns: [
                { field: 'inbound_code', title: '入库单号' },
                { field: 'part_code', title: '备件编号' },
                { field: 'part_name', title: '备件名称' },
                { field: 'source_type', title: '来源', render: (v) => v === 'purchase' ? '采购入库' : '退库' },
                { field: 'batch_no', title: '批次号', render: (v) => v || '-' },
                { field: 'quantity', title: '数量' },
                { field: 'unit_price', title: '单价', render: (v) => `¥${v?.toFixed(2) || 0}` },
                { field: 'total_price', title: '总价', render: (v) => `¥${v?.toFixed(2) || 0}` },
                { field: 'operator', title: '操作人' },
                { field: 'inbound_time', title: '入库时间' },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id) => `
                        <button class="btn btn-sm btn-danger" onclick="SparePage.deleteInbound(${id})">删除</button>
                    `
                }
            ],
            data: data
        });
    },

    async showInboundModal() {
        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">新增入库</h4>
                <form id="inboundForm">
                    <div class="form-group">
                        <label>选择备件 *</label>
                        <select class="form-control" name="spare_part_id" required onchange="SpareService.getPartById(this.value).then(r => { if(r.code===200){document.getElementById('suggestPrice').value=r.data.unit_price} })">
                            <option value="">请选择备件</option>
                            ${this.parts.map(p => `<option value="${p.id}">${p.part_code} - ${p.part_name} (库存: ${p.current_stock})</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>来源 *</label>
                            <select class="form-control" name="source_type" required>
                                <option value="purchase">采购入库</option>
                                <option value="return">退库</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>批次号</label>
                            <input type="text" class="form-control" name="batch_no">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>入库数量 *</label>
                            <input type="number" class="form-control" name="quantity" min="1" required>
                        </div>
                        <div class="form-group">
                            <label>单价 (元)</label>
                            <input type="number" class="form-control" name="unit_price" id="suggestPrice" min="0" step="0.01">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>操作人</label>
                        <input type="text" class="form-control" name="operator" value="${AuthService.getCurrentUser()?.username || ''}">
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea class="form-control" name="remark" rows="2"></textarea>
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: '新增入库',
            content: html,
            width: 500,
            onConfirm: async () => {
                const form = document.getElementById('inboundForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (['spare_part_id', 'quantity'].includes(key)) {
                        data[key] = parseInt(value);
                    } else if (key === 'unit_price') {
                        data[key] = parseFloat(value) || 0;
                    } else {
                        data[key] = value;
                    }
                });

                try {
                    const res = await SpareService.createInbound(data);
                    if (res.code === 201) {
                        Toast.success('入库成功');
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

    async deleteInbound(id) {
        const confirmed = await Modal.confirm('确定要删除该入库记录吗？删除后库存将回退。');
        if (!confirmed) return;
        try {
            const res = await SpareService.deleteInbound(id);
            if (res.code === 200) {
                Toast.success('删除成功');
                this.loadData();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('删除失败');
        }
    },

    renderOutboundTab(container) {
        container.innerHTML = `
            <div class="toolbar">
                <div class="toolbar-left">
                    <select class="form-control" id="outboundPartFilter" style="width: 180px;">
                        <option value="">全部备件</option>
                        ${this.parts.map(p => `<option value="${p.id}">${p.part_name}</option>`).join('')}
                    </select>
                    <label style="margin-left: 12px; display: flex; align-items: center;">
                        <input type="checkbox" id="outboundReturnedFilter" style="margin-right: 6px;">
                        仅显示未归还
                    </label>
                </div>
                <div class="toolbar-right">
                    <button class="btn btn-primary" onclick="SparePage.showOutboundModal()">
                        + 新增领用
                    </button>
                </div>
            </div>
            <div id="outboundTable"></div>
        `;

        document.getElementById('outboundPartFilter')?.addEventListener('change', () => this.filterOutbounds());
        document.getElementById('outboundReturnedFilter')?.addEventListener('change', () => this.filterOutbounds());
    },

    async loadOutbounds() {
        try {
            const res = await SpareService.getOutbounds({ size: 1000 });
            if (res.code === 200) {
                this.outbounds = res.data?.items || [];
                this.renderOutboundTable();
            }
        } catch (error) {
            Toast.error('加载领用列表失败');
        }
    },

    filterOutbounds() {
        const partId = document.getElementById('outboundPartFilter')?.value;
        const notReturnedOnly = document.getElementById('outboundReturnedFilter')?.checked;

        let filtered = [...this.outbounds];
        if (partId) filtered = filtered.filter(o => o.spare_part_id === parseInt(partId));
        if (notReturnedOnly) filtered = filtered.filter(o => o.is_returned === 0);

        this.renderOutboundTable(filtered);
    },

    renderOutboundTable(data = this.outbounds) {
        const container = document.getElementById('outboundTable');
        if (!container) return;

        new DataTable('#outboundTable', {
            columns: [
                { field: 'outbound_code', title: '领用单号' },
                { field: 'part_code', title: '备件编号' },
                { field: 'part_name', title: '备件名称' },
                { field: 'order_code', title: '关联工单', render: (v) => v || '-' },
                { field: 'reason', title: '领用原因', render: (v) => v || '-' },
                { field: 'quantity', title: '数量' },
                { field: 'receiver', title: '领用人' },
                { field: 'outbound_time', title: '领用时间' },
                { 
                    field: 'is_returned', 
                    title: '状态', 
                    render: (v) => v === 1 ? '<span class="badge badge-success">已归还</span>' : '<span class="badge badge-warning">未归还</span>'
                },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id, row) => {
                        const buttons = [];
                        if (row.is_returned === 0) {
                            buttons.push(`<button class="btn btn-sm btn-success" onclick="SparePage.returnOutbound(${id})">归还</button>`);
                        }
                        buttons.push(`<button class="btn btn-sm btn-danger" onclick="SparePage.deleteOutbound(${id})" style="margin-left: 4px;">删除</button>`);
                        return buttons.join('');
                    }
                }
            ],
            data: data
        });
    },

    async showOutboundModal() {
        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">新增领用</h4>
                <form id="outboundForm">
                    <div class="form-group">
                        <label>选择备件 *</label>
                        <select class="form-control" name="spare_part_id" required onchange="SpareService.getPartById(this.value).then(r => { if(r.code===200){document.getElementById('stockInfo').textContent='当前库存: '+r.data.current_stock} })">
                            <option value="">请选择备件</option>
                            ${this.parts.map(p => `<option value="${p.id}">${p.part_code} - ${p.part_name} (库存: ${p.current_stock})</option>`).join('')}
                        </select>
                        <small id="stockInfo" style="color: var(--text-secondary); margin-top: 4px; display: block;"></small>
                    </div>
                    <div class="form-group">
                        <label>关联维修工单</label>
                        <select class="form-control" name="work_order_id">
                            <option value="">不关联工单</option>
                            ${this.workOrders.filter(o => o.status !== 'completed' && o.status !== 'cancelled').map(o => 
                                `<option value="${o.id}">${o.order_code} - ${o.order_name}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>领用原因（不关联工单时必填）</label>
                        <input type="text" class="form-control" name="reason" placeholder="自定义领用原因">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>领用数量 *</label>
                            <input type="number" class="form-control" name="quantity" min="1" required>
                        </div>
                        <div class="form-group">
                            <label>领用人 *</label>
                            <input type="text" class="form-control" name="receiver" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>操作人</label>
                        <input type="text" class="form-control" name="operator" value="${AuthService.getCurrentUser()?.username || ''}">
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea class="form-control" name="remark" rows="2"></textarea>
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: '新增领用',
            content: html,
            width: 550,
            onConfirm: async () => {
                const form = document.getElementById('outboundForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (['spare_part_id', 'work_order_id', 'quantity'].includes(key)) {
                        data[key] = value ? parseInt(value) : null;
                    } else {
                        data[key] = value;
                    }
                });

                if (!data.work_order_id && !data.reason) {
                    Toast.error('请选择关联工单或填写领用原因');
                    return;
                }

                try {
                    const res = await SpareService.createOutbound(data);
                    if (res.code === 201) {
                        Toast.success('领用成功');
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

    async returnOutbound(id) {
        const confirmed = await Modal.confirm('确定要归还该备件吗？');
        if (!confirmed) return;
        try {
            const res = await SpareService.returnOutbound(id);
            if (res.code === 200) {
                Toast.success('归还成功');
                this.loadData();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    },

    async deleteOutbound(id) {
        const confirmed = await Modal.confirm('确定要删除该领用记录吗？');
        if (!confirmed) return;
        try {
            const res = await SpareService.deleteOutbound(id);
            if (res.code === 200) {
                Toast.success('删除成功');
                this.loadData();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('删除失败');
        }
    },

    renderInventoryTab(container) {
        const currentMonth = new Date().toISOString().slice(0, 7);
        container.innerHTML = `
            <div class="toolbar">
                <div class="toolbar-left">
                    <input type="month" class="form-control" id="inventoryMonth" value="${currentMonth}" style="width: 150px;">
                    <label style="margin-left: 12px; display: flex; align-items: center;">
                        <input type="checkbox" id="inventoryDiffFilter" style="margin-right: 6px;">
                        仅显示有差异
                    </label>
                </div>
                <div class="toolbar-right">
                    <button class="btn btn-outline" onclick="SparePage.batchCreateInventory()">批量生成盘点</button>
                    <button class="btn btn-primary" onclick="SparePage.showInventoryModal()" style="margin-left: 8px;">
                        + 新增盘点
                    </button>
                </div>
            </div>
            <div id="inventoryTable"></div>
        `;

        document.getElementById('inventoryMonth')?.addEventListener('change', () => this.loadInventories());
        document.getElementById('inventoryDiffFilter')?.addEventListener('change', () => this.filterInventories());
    },

    async loadInventories() {
        const month = document.getElementById('inventoryMonth')?.value;
        try {
            const res = await SpareService.getInventories({ size: 1000, inventoryMonth: month });
            if (res.code === 200) {
                this.inventories = res.data?.items || [];
                this.renderInventoryTable();
            }
        } catch (error) {
            Toast.error('加载盘点列表失败');
        }
    },

    filterInventories() {
        const hasDiff = document.getElementById('inventoryDiffFilter')?.checked;
        let filtered = [...this.inventories];
        if (hasDiff) filtered = filtered.filter(i => i.difference !== 0);
        this.renderInventoryTable(filtered);
    },

    renderInventoryTable(data = this.inventories) {
        const container = document.getElementById('inventoryTable');
        if (!container) return;

        new DataTable('#inventoryTable', {
            columns: [
                { field: 'inventory_code', title: '盘点单号' },
                { field: 'inventory_month', title: '盘点月份' },
                { field: 'part_code', title: '备件编号' },
                { field: 'part_name', title: '备件名称' },
                { field: 'book_stock', title: '账面库存' },
                { field: 'actual_stock', title: '实物库存' },
                { 
                    field: 'difference', 
                    title: '差异数量',
                    render: (v) => {
                        let color = 'inherit';
                        if (v > 0) color = '#28a745';
                        else if (v < 0) color = '#dc3545';
                        return `<span style="color: ${color}; font-weight: bold;">${v}</span>`;
                    }
                },
                { field: 'difference_reason', title: '差异原因', render: (v) => v || '-' },
                { field: 'operator', title: '盘点人' },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id) => `
                        <button class="btn btn-sm btn-outline" onclick="SparePage.showInventoryModal(${id})">编辑</button>
                        <button class="btn btn-sm btn-danger" onclick="SparePage.deleteInventory(${id})" style="margin-left: 4px;">删除</button>
                    `
                }
            ],
            data: data
        });
    },

    async showInventoryModal(id = null) {
        const inv = id ? this.inventories.find(i => i.id === id) : null;
        const isEdit = !!inv;
        const currentMonth = new Date().toISOString().slice(0, 7);

        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">${isEdit ? '编辑' : '新增'}盘点</h4>
                <form id="inventoryForm">
                    <div class="form-group">
                        <label>盘点月份 *</label>
                        <input type="month" class="form-control" name="inventory_month" value="${inv?.inventory_month || currentMonth}" required>
                    </div>
                    <div class="form-group">
                        <label>选择备件 *</label>
                        <select class="form-control" name="spare_part_id" ${isEdit ? 'disabled' : ''} required onchange="SpareService.getPartById(this.value).then(r => { if(r.code===200){document.getElementById('bookStock').value=r.data.current_stock} })">
                            <option value="">请选择备件</option>
                            ${this.parts.map(p => `<option value="${p.id}" ${inv?.spare_part_id === p.id ? 'selected' : ''}>${p.part_code} - ${p.part_name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>账面库存</label>
                            <input type="number" class="form-control" name="book_stock" id="bookStock" value="${inv?.book_stock || ''}" readonly>
                        </div>
                        <div class="form-group">
                            <label>实物库存 *</label>
                            <input type="number" class="form-control" name="actual_stock" value="${inv?.actual_stock || ''}" min="0" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>差异原因</label>
                        <textarea class="form-control" name="difference_reason" rows="2">${inv?.difference_reason || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>盘点人</label>
                        <input type="text" class="form-control" name="operator" value="${inv?.operator || AuthService.getCurrentUser()?.username || ''}">
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: isEdit ? '编辑盘点' : '新增盘点',
            content: html,
            width: 500,
            onConfirm: async () => {
                const form = document.getElementById('inventoryForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (['spare_part_id', 'book_stock', 'actual_stock'].includes(key)) {
                        data[key] = parseInt(value) || 0;
                    } else {
                        data[key] = value;
                    }
                });

                try {
                    let res;
                    if (isEdit) {
                        res = await SpareService.updateInventory(id, data);
                    } else {
                        res = await SpareService.createInventory(data);
                    }
                    if (res.code === 200 || res.code === 201) {
                        Toast.success(isEdit ? '更新成功' : '创建成功');
                        Modal.close();
                        this.loadInventories();
                    } else {
                        Toast.error(res.message);
                    }
                } catch (error) {
                    Toast.error('操作失败');
                }
            }
        });
    },

    async batchCreateInventory() {
        const month = document.getElementById('inventoryMonth')?.value;
        const confirmed = await Modal.confirm(`确定要为 ${month} 批量生成所有备件的盘点记录吗？`);
        if (!confirmed) return;
        try {
            const res = await SpareService.batchCreateInventory({ inventory_month: month });
            if (res.code === 200) {
                Toast.success(`成功生成 ${res.data?.created_count || 0} 条盘点记录`);
                this.loadInventories();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    },

    async deleteInventory(id) {
        const confirmed = await Modal.confirm('确定要删除该盘点记录吗？');
        if (!confirmed) return;
        try {
            const res = await SpareService.deleteInventory(id);
            if (res.code === 200) {
                Toast.success('删除成功');
                this.loadInventories();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('删除失败');
        }
    },

    renderTurnoverTab(container) {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setMonth(startDate.getMonth() - 1);

        container.innerHTML = `
            <div class="toolbar">
                <div class="toolbar-left">
                    <label style="margin-right: 8px;">统计周期:</label>
                    <input type="date" class="form-control" id="turnoverStartDate" value="${startDate.toISOString().slice(0, 10)}" style="width: 150px;">
                    <span style="margin: 0 8px;">至</span>
                    <input type="date" class="form-control" id="turnoverEndDate" value="${endDate.toISOString().slice(0, 10)}" style="width: 150px;">
                    <button class="btn btn-primary" onclick="SparePage.loadTurnoverRates()" style="margin-left: 8px;">查询</button>
                </div>
                <div class="toolbar-right">
                    <span style="color: var(--text-secondary); font-size: 13px;">周转率 = 出库量 / 平均库存</span>
                </div>
            </div>
            <div id="turnoverTable"></div>
        `;
    },

    async loadTurnoverRates() {
        const startDate = document.getElementById('turnoverStartDate')?.value;
        const endDate = document.getElementById('turnoverEndDate')?.value;
        try {
            const res = await SpareService.getTurnoverRate({ startDate, endDate, topN: 20 });
            if (res.code === 200) {
                this.turnoverRates = res.data?.items || [];
                this.renderTurnoverTable(res.data);
            }
        } catch (error) {
            Toast.error('加载周转率数据失败');
        }
    },

    renderTurnoverTable(data) {
        const container = document.getElementById('turnoverTable');
        if (!container) return;

        const items = this.turnoverRates.map((item, index) => ({
            ...item,
            rank: index + 1
        }));

        new DataTable('#turnoverTable', {
            columns: [
                { 
                    field: 'rank', 
                    title: '排名',
                    render: (v) => {
                        if (v === 1) return '🥇';
                        if (v === 2) return '🥈';
                        if (v === 3) return '🥉';
                        return v;
                    }
                },
                { field: 'part_code', title: '备件编号' },
                { field: 'part_name', title: '备件名称' },
                { field: 'specification', title: '规格', render: (v) => v || '-' },
                { field: 'start_stock', title: '期初库存' },
                { field: 'end_stock', title: '期末库存' },
                { field: 'avg_stock', title: '平均库存' },
                { field: 'outbound_quantity', title: '出库量' },
                { field: 'inbound_quantity', title: '入库量' },
                { 
                    field: 'turnover_rate', 
                    title: '周转率',
                    render: (v) => {
                        let color = '#28a745';
                        if (v < 0.5) color = '#dc3545';
                        else if (v < 1) color = '#ffc107';
                        return `<span style="color: ${color}; font-weight: bold;">${(v * 100).toFixed(2)}%</span>`;
                    }
                }
            ],
            data: items
        });
    },

    destroy() {
    }
};

window.SparePage = SparePage;
