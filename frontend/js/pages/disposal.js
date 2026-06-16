/**
 * 不合格品处置页面
 */
const DisposalPage = {
    currentTab: 'list',
    orders: [],
    pendingApprovals: [],
    dashboard: null,
    monthlyStats: null,
    trendStats: null,
    pieChart: null,
    lineChart: null,
    equipments: [],

    init() {
        this.render();
        this.loadData();
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 class="card-title">不合格品处置</h3>
                    <div id="dashboardSummary" style="display: flex; gap: 16px; font-size: 13px;">
                    </div>
                </div>
                <div class="card-body">
                    <div class="safety-tab-bar" style="margin-bottom: 20px;">
                        <div class="safety-tab active" data-tab="list" onclick="DisposalPage.switchTab('list')">
                            📋 待处置单列表
                        </div>
                        <div class="safety-tab" data-tab="approval" onclick="DisposalPage.switchTab('approval')">
                            ✅ 审批工作台
                        </div>
                        <div class="safety-tab" data-tab="statistics" onclick="DisposalPage.switchTab('statistics')">
                            📊 处置统计看板
                        </div>
                    </div>
                    <div id="tabContent"></div>
                </div>
            </div>
        `;
    },

    async loadData() {
        try {
            const [equipRes, dashboardRes] = await Promise.all([
                ProductionService.getEquipments({ size: 1000 }),
                DisposalService.getDashboard()
            ]);

            if (equipRes.code === 200) this.equipments = equipRes.data?.items || [];
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
                <span style="color: var(--text-secondary);">总数:</span>
                <strong style="margin-left: 6px;">${this.dashboard.total_orders}</strong>
            </div>
            <div style="padding: 8px 16px; background: ${this.dashboard.pending_orders > 0 ? '#fff3cd' : 'var(--bg-light)'}; border-radius: 6px;">
                <span style="color: var(--text-secondary);">待审批:</span>
                <strong style="margin-left: 6px; color: ${this.dashboard.pending_orders > 0 ? '#dc3545' : 'inherit'};">${this.dashboard.pending_orders}</strong>
            </div>
            <div style="padding: 8px 16px; background: var(--bg-light); border-radius: 6px;">
                <span style="color: var(--text-secondary);">已完成:</span>
                <strong style="margin-left: 6px;">${this.dashboard.completed_orders}</strong>
            </div>
            <div style="padding: 8px 16px; background: var(--bg-light); border-radius: 6px;">
                <span style="color: var(--text-secondary);">累计损失:</span>
                <strong style="margin-left: 6px; color: #dc3545;">¥${this.dashboard.total_loss?.toFixed(2) || 0}</strong>
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
            case 'list':
                this.renderListTab(content);
                this.loadOrders();
                break;
            case 'approval':
                this.renderApprovalTab(content);
                this.loadPendingApprovals();
                break;
            case 'statistics':
                this.renderStatisticsTab(content);
                this.loadStatistics();
                break;
        }
    },

    getStatusText(status) {
        const map = {
            'draft': '草稿',
            'pending_approval': '待审批',
            'approved': '已通过',
            'rejected': '已驳回',
            'returned': '已退回',
            'processing': '处理中',
            'completed': '已完成'
        };
        return map[status] || status;
    },

    getStatusBadge(status) {
        const colorMap = {
            'draft': 'secondary',
            'pending_approval': 'warning',
            'approved': 'primary',
            'rejected': 'danger',
            'returned': 'warning',
            'processing': 'info',
            'completed': 'success'
        };
        const badgeClass = colorMap[status] || 'secondary';
        return `<span class="badge badge-${badgeClass}">${this.getStatusText(status)}</span>`;
    },

    getDisposalText(type) {
        const map = {
            'rework': '返工',
            'concession': '让步接收',
            'scrap': '报废'
        };
        return map[type] || type;
    },

    getSourceText(source) {
        const map = {
            'quality_check': '质检不合格',
            'inspection': '巡检',
            'manual': '手工录入'
        };
        return map[source] || source;
    },

    renderListTab(container) {
        container.innerHTML = `
            <div class="toolbar">
                <div class="toolbar-left">
                    <select class="form-control" id="statusFilter" style="width: 120px;">
                        <option value="">全部状态</option>
                        <option value="draft">草稿</option>
                        <option value="pending_approval">待审批</option>
                        <option value="approved">已通过</option>
                        <option value="rejected">已驳回</option>
                        <option value="returned">已退回</option>
                        <option value="completed">已完成</option>
                    </select>
                    <select class="form-control" id="disposalFilter" style="width: 120px; margin-left: 8px;">
                        <option value="">全部处置方式</option>
                        <option value="rework">返工</option>
                        <option value="concession">让步接收</option>
                        <option value="scrap">报废</option>
                    </select>
                    <select class="form-control" id="sourceFilter" style="width: 120px; margin-left: 8px;">
                        <option value="">全部来源</option>
                        <option value="quality_check">质检不合格</option>
                        <option value="inspection">巡检</option>
                        <option value="manual">手工录入</option>
                    </select>
                    <input type="text" class="form-control" id="orderSearch" 
                           placeholder="搜索单号、产品、缺陷..." 
                           style="width: 200px; margin-left: 8px;">
                </div>
                <div class="toolbar-right">
                    <button class="btn btn-primary" onclick="DisposalPage.showOrderModal()">
                        + 新增待处置单
                    </button>
                </div>
            </div>
            <div id="ordersTable"></div>
        `;

        document.getElementById('statusFilter')?.addEventListener('change', () => this.filterOrders());
        document.getElementById('disposalFilter')?.addEventListener('change', () => this.filterOrders());
        document.getElementById('sourceFilter')?.addEventListener('change', () => this.filterOrders());
        document.getElementById('orderSearch')?.addEventListener('input', () => this.filterOrders());
    },

    async loadOrders() {
        try {
            const res = await DisposalService.getOrders({ size: 1000 });
            if (res.code === 200) {
                this.orders = res.data?.items || [];
                this.renderOrdersTable();
            }
        } catch (error) {
            Toast.error('加载待处置单列表失败');
        }
    },

    filterOrders() {
        const status = document.getElementById('statusFilter')?.value || '';
        const disposalType = document.getElementById('disposalFilter')?.value || '';
        const sourceType = document.getElementById('sourceFilter')?.value || '';
        const keyword = document.getElementById('orderSearch')?.value?.toLowerCase() || '';

        let filtered = [...this.orders];
        if (status) filtered = filtered.filter(o => o.status === status);
        if (disposalType) filtered = filtered.filter(o => o.suggested_disposal === disposalType);
        if (sourceType) filtered = filtered.filter(o => o.source_type === sourceType);
        if (keyword) {
            filtered = filtered.filter(o =>
                o.order_code?.toLowerCase().includes(keyword) ||
                o.related_name?.toLowerCase().includes(keyword) ||
                o.defect_description?.toLowerCase().includes(keyword)
            );
        }

        this.renderOrdersTable(filtered);
    },

    renderOrdersTable(data = this.orders) {
        const container = document.getElementById('ordersTable');
        if (!container) return;

        new DataTable('#ordersTable', {
            columns: [
                { field: 'order_code', title: '处置单号' },
                { 
                    field: 'source_type', 
                    title: '来源',
                    render: (v) => this.getSourceText(v)
                },
                { 
                    field: 'related_type', 
                    title: '关联类型',
                    render: (v) => v === 'product' ? '产品' : '设备'
                },
                { field: 'related_name', title: '关联名称' },
                { field: 'quantity', title: '数量' },
                { 
                    field: 'suggested_disposal', 
                    title: '处置建议',
                    render: (v) => this.getDisposalText(v)
                },
                { field: 'applicant', title: '申请人' },
                { field: 'apply_time', title: '申请时间' },
                { 
                    field: 'status', 
                    title: '状态',
                    render: (v) => this.getStatusBadge(v)
                },
                { 
                    field: 'current_approval_level', 
                    title: '审批进度',
                    render: (v, row) => {
                        if (row.status === 'draft') return '未提交';
                        if (row.status === 'completed') return '已完成';
                        if (row.status === 'rejected') return '已驳回';
                        if (row.status === 'returned') return '已退回';
                        const level = parseInt(v) || 0;
                        if (level === 1) return '班组长审批中';
                        if (level === 2) return '部门主管审批中';
                        if (level === 3) return '审批通过';
                        return '-';
                    }
                },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id, row) => this.renderOrderActions(id, row)
                }
            ],
            data: data
        });
    },

    renderOrderActions(id, row) {
        const buttons = [];
        buttons.push(`<button class="btn btn-sm btn-outline" onclick="DisposalPage.showOrderDetail(${id})">查看</button>`);

        if (row.status === 'draft' || row.status === 'returned') {
            buttons.push(`<button class="btn btn-sm btn-primary" onclick="DisposalPage.showOrderModal(${id})" style="margin-left: 4px;">编辑</button>`);
            buttons.push(`<button class="btn btn-sm btn-success" onclick="DisposalPage.submitOrder(${id})" style="margin-left: 4px;">提交</button>`);
        }

        if (row.status === 'approved' && !row.disposal_result) {
            buttons.push(`<button class="btn btn-sm btn-info" onclick="DisposalPage.showResultModal(${id})" style="margin-left: 4px;">记录结果</button>`);
        }

        if (row.status === 'draft' || row.status === 'rejected') {
            buttons.push(`<button class="btn btn-sm btn-danger" onclick="DisposalPage.deleteOrder(${id})" style="margin-left: 4px;">删除</button>`);
        }

        return buttons.join('');
    },

    async showOrderModal(id = null) {
        const order = id ? this.orders.find(o => o.id === id) : null;
        const isEdit = !!order;

        const html = `
            <div style="padding: 20px; max-height: 70vh; overflow-y: auto;">
                <h4 style="margin-bottom: 20px;">${isEdit ? '编辑' : '新增'}待处置单</h4>
                <form id="orderForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label>来源 *</label>
                            <select class="form-control" name="source_type" required>
                                <option value="manual" ${order?.source_type === 'manual' ? 'selected' : ''}>手工录入</option>
                                <option value="quality_check" ${order?.source_type === 'quality_check' ? 'selected' : ''}>质检不合格</option>
                                <option value="inspection" ${order?.source_type === 'inspection' ? 'selected' : ''}>巡检</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>来源记录编号</label>
                            <input type="text" class="form-control" name="source_code" value="${order?.source_code || ''}">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>关联类型 *</label>
                            <select class="form-control" name="related_type" required onchange="DisposalPage.toggleRelatedSelect(this.value)">
                                <option value="equipment" ${order?.related_type === 'equipment' ? 'selected' : ''}>设备</option>
                                <option value="product" ${order?.related_type === 'product' ? 'selected' : ''}>产品</option>
                            </select>
                        </div>
                        <div class="form-group" id="relatedEquipmentGroup">
                            <label>关联设备 *</label>
                            <select class="form-control" name="related_id" ${order?.related_type === 'product' ? 'disabled' : ''} required>
                                <option value="">请选择设备</option>
                                ${this.equipments.map(e => `<option value="${e.id}" ${order?.related_id === e.id ? 'selected' : ''}>${e.equipment_code} - ${e.equipment_name}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group" id="relatedProductGroup" style="display: ${order?.related_type === 'product' ? 'block' : 'none'};">
                            <label>产品信息 *</label>
                            <input type="text" class="form-control" name="related_name" placeholder="产品名称" value="${order?.related_name || ''}" ${order?.related_type === 'equipment' ? 'disabled' : ''}>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>数量 *</label>
                            <input type="number" class="form-control" name="quantity" value="${order?.quantity || 1}" min="1" required>
                        </div>
                        <div class="form-group">
                            <label>单位</label>
                            <input type="text" class="form-control" name="unit" value="${order?.unit || '件'}">
                        </div>
                        <div class="form-group">
                            <label>单价 (元)</label>
                            <input type="number" class="form-control" name="unit_price" value="${order?.unit_price || 0}" min="0" step="0.01">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>缺陷描述 *</label>
                        <textarea class="form-control" name="defect_description" rows="3" required>${order?.defect_description || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>处置建议 *</label>
                        <select class="form-control" name="suggested_disposal" required>
                            <option value="">请选择</option>
                            <option value="rework" ${order?.suggested_disposal === 'rework' ? 'selected' : ''}>返工</option>
                            <option value="concession" ${order?.suggested_disposal === 'concession' ? 'selected' : ''}>让步接收</option>
                            <option value="scrap" ${order?.suggested_disposal === 'scrap' ? 'selected' : ''}>报废</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>附件 (图片base64)</label>
                        <textarea class="form-control" name="attachment" rows="2" placeholder="粘贴图片base64编码">${order?.attachment || ''}</textarea>
                        <small class="form-text text-muted">可上传图片并粘贴base64编码</small>
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea class="form-control" name="remark" rows="2">${order?.remark || ''}</textarea>
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: isEdit ? '编辑待处置单' : '新增待处置单',
            content: html,
            width: 700,
            onConfirm: async () => {
                const form = document.getElementById('orderForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (key === 'related_id') {
                        data[key] = value ? parseInt(value) : null;
                    } else if (key === 'quantity') {
                        data[key] = parseInt(value) || 1;
                    } else if (key === 'unit_price') {
                        data[key] = parseFloat(value) || 0;
                    } else {
                        data[key] = value;
                    }
                });

                if (data.related_type === 'product') {
                    data.related_id = null;
                    data.related_code = '';
                }

                try {
                    let res;
                    if (isEdit) {
                        res = await DisposalService.updateOrder(id, data);
                    } else {
                        res = await DisposalService.createOrder(data);
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

    toggleRelatedSelect(type) {
        const equipGroup = document.getElementById('relatedEquipmentGroup');
        const productGroup = document.getElementById('relatedProductGroup');
        const equipSelect = equipGroup?.querySelector('select');
        const productInput = productGroup?.querySelector('input');

        if (type === 'equipment') {
            equipGroup.style.display = 'block';
            productGroup.style.display = 'none';
            if (equipSelect) equipSelect.disabled = false;
            if (productInput) productInput.disabled = true;
        } else {
            equipGroup.style.display = 'none';
            productGroup.style.display = 'block';
            if (equipSelect) equipSelect.disabled = true;
            if (productInput) productInput.disabled = false;
        }
    },

    async showOrderDetail(id) {
        try {
            const res = await DisposalService.getOrderById(id);
            if (res.code !== 200) {
                Toast.error('获取详情失败');
                return;
            }
            const order = res.data;

            const approvalList = (order.approval_list || []).map(a => `
                <div style="padding: 12px; background: var(--bg-light); border-radius: 6px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <strong>${a.approval_role} - ${a.approver}</strong>
                        <span style="color: var(--text-secondary); font-size: 12px;">${a.approval_time || ''}</span>
                    </div>
                    <div style="margin-bottom: 4px;">
                        <span class="badge badge-${a.action === 'approve' ? 'success' : a.action === 'reject' ? 'danger' : 'warning'}">
                            ${a.action === 'approve' ? '通过' : a.action === 'reject' ? '驳回' : '退回'}
                        </span>
                    </div>
                    ${a.opinion ? `<div style="font-size: 13px;">意见: ${a.opinion}</div>` : ''}
                </div>
            `).join('') || '<p class="empty-text">暂无审批记录</p>';

            const resultHtml = order.disposal_result ? `
                <div style="padding: 16px; background: #d4edda; border-radius: 6px; margin-top: 16px;">
                    <h5 style="margin-bottom: 12px; color: #155724;">处置结果</h5>
                    <div class="form-row">
                        <div class="form-group">
                            <label>最终决定</label>
                            <div><strong>${this.getDisposalText(order.disposal_result.final_decision)}</strong></div>
                        </div>
                        <div class="form-group">
                            <label>操作人</label>
                            <div>${order.disposal_result.operator || ''}</div>
                        </div>
                        <div class="form-group">
                            <label>操作时间</label>
                            <div>${order.disposal_result.operate_time || ''}</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>损失估算</label>
                            <div style="color: #dc3545; font-weight: bold;">¥${order.disposal_result.loss_estimate?.toFixed(2) || 0}</div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>操作记录</label>
                        <div>${order.disposal_result.operation_record || ''}</div>
                    </div>
                </div>
            ` : '';

            const html = `
                <div style="padding: 20px; max-height: 70vh; overflow-y: auto;">
                    <h4 style="margin-bottom: 20px;">待处置单详情 - ${order.order_code}</h4>
                    <div class="form-row">
                        <div class="form-group">
                            <label>来源</label>
                            <div>${this.getSourceText(order.source_type)}</div>
                        </div>
                        <div class="form-group">
                            <label>来源编号</label>
                            <div>${order.source_code || '-'}</div>
                        </div>
                        <div class="form-group">
                            <label>状态</label>
                            <div>${this.getStatusBadge(order.status)}</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>关联类型</label>
                            <div>${order.related_type === 'product' ? '产品' : '设备'}</div>
                        </div>
                        <div class="form-group">
                            <label>关联名称</label>
                            <div>${order.related_name || '-'}</div>
                        </div>
                        <div class="form-group">
                            <label>关联编号</label>
                            <div>${order.related_code || '-'}</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>数量</label>
                            <div>${order.quantity} ${order.unit || '件'}</div>
                        </div>
                        <div class="form-group">
                            <label>单价</label>
                            <div>¥${order.unit_price?.toFixed(2) || 0}</div>
                        </div>
                        <div class="form-group">
                            <label>处置建议</label>
                            <div>${this.getDisposalText(order.suggested_disposal)}</div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>缺陷描述</label>
                        <div style="padding: 12px; background: var(--bg-light); border-radius: 6px;">${order.defect_description || ''}</div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>申请人</label>
                            <div>${order.applicant || ''}</div>
                        </div>
                        <div class="form-group">
                            <label>申请时间</label>
                            <div>${order.apply_time || ''}</div>
                        </div>
                    </div>
                    ${order.attachment ? `
                    <div class="form-group">
                        <label>附件</label>
                        <div><img src="${order.attachment}" style="max-width: 300px; max-height: 200px; border-radius: 6px;"></div>
                    </div>
                    ` : ''}
                    <h5 style="margin: 20px 0 12px;">审批记录</h5>
                    ${approvalList}
                    ${resultHtml}
                </div>
            `;

            Modal.show({
                title: '待处置单详情',
                content: html,
                width: 700,
                showConfirm: false,
                cancelText: '关闭'
            });
        } catch (error) {
            Toast.error('获取详情失败');
        }
    },

    async submitOrder(id) {
        const confirmed = await Modal.confirm('确定要提交该待处置单进入审批流程吗？');
        if (!confirmed) return;
        try {
            const res = await DisposalService.submitOrder(id);
            if (res.code === 200) {
                Toast.success('提交成功');
                this.loadOrders();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('提交失败');
        }
    },

    async deleteOrder(id) {
        const confirmed = await Modal.confirm('确定要删除该待处置单吗？');
        if (!confirmed) return;
        try {
            const res = await DisposalService.deleteOrder(id);
            if (res.code === 200) {
                Toast.success('删除成功');
                this.loadOrders();
            } else {
                Toast.error(res.message);
            }
        } catch (error) {
            Toast.error('删除失败');
        }
    },

    async showResultModal(id) {
        const order = this.orders.find(o => o.id === id);
        if (!order) return;

        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">记录处置结果</h4>
                <div style="padding: 12px; background: var(--bg-light); border-radius: 6px; margin-bottom: 16px;">
                    <div><strong>${order.order_code}</strong> - ${order.related_name} (${order.quantity} ${order.unit || '件'})</div>
                    <div style="margin-top: 4px; color: var(--text-secondary);">建议处置: ${this.getDisposalText(order.suggested_disposal)}</div>
                </div>
                <form id="resultForm">
                    <div class="form-group">
                        <label>最终决定 *</label>
                        <select class="form-control" name="final_decision" required onchange="DisposalPage.updateLossEstimate(this.value)">
                            <option value="">请选择</option>
                            <option value="rework">返工</option>
                            <option value="concession">让步接收</option>
                            <option value="scrap">报废</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>损失估算 (元)</label>
                        <input type="number" class="form-control" name="loss_estimate" id="lossEstimate" value="0" min="0" step="0.01">
                        <small class="form-text text-muted">报废按单价×数量自动计算，返工按20元/件估算，可手动调整</small>
                    </div>
                    <div class="form-group">
                        <label>操作记录 *</label>
                        <textarea class="form-control" name="operation_record" rows="3" required placeholder="请详细描述处置过程..."></textarea>
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
            title: '记录处置结果',
            content: html,
            width: 550,
            onConfirm: async () => {
                const form = document.getElementById('resultForm');
                const formData = new FormData(form);
                const data = {};
                formData.forEach((value, key) => {
                    if (key === 'loss_estimate') {
                        data[key] = parseFloat(value) || 0;
                    } else {
                        data[key] = value;
                    }
                });

                try {
                    const res = await DisposalService.recordResult(id, data);
                    if (res.code === 200) {
                        Toast.success('处置结果已记录');
                        Modal.close();
                        this.loadOrders();
                    } else {
                        Toast.error(res.message);
                    }
                } catch (error) {
                    Toast.error('操作失败');
                }
            }
        });

        this._currentOrderForResult = order;
    },

    updateLossEstimate(decision) {
        const order = this._currentOrderForResult;
        if (!order) return;

        let loss = 0;
        if (decision === 'scrap') {
            loss = order.quantity * (parseFloat(order.unit_price) || 0);
        } else if (decision === 'rework') {
            loss = order.quantity * 20;
        }

        const input = document.getElementById('lossEstimate');
        if (input) input.value = loss.toFixed(2);
    },

    renderApprovalTab(container) {
        container.innerHTML = `
            <div class="toolbar">
                <div class="toolbar-left">
                    <span style="font-size: 14px; color: var(--text-secondary);">
                        显示需要您审批的待处置单
                    </span>
                </div>
            </div>
            <div id="approvalTable"></div>
        `;
    },

    async loadPendingApprovals() {
        try {
            const res = await DisposalService.getMyPendingApprovals({ size: 1000 });
            if (res.code === 200) {
                this.pendingApprovals = res.data?.items || [];
                this.renderApprovalTable();
            }
        } catch (error) {
            Toast.error('加载待审批列表失败');
        }
    },

    renderApprovalTable(data = this.pendingApprovals) {
        const container = document.getElementById('approvalTable');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<p class="empty-text">暂无待审批的单据</p>';
            return;
        }

        new DataTable('#approvalTable', {
            columns: [
                { field: 'order_code', title: '处置单号' },
                { 
                    field: 'source_type', 
                    title: '来源',
                    render: (v) => this.getSourceText(v)
                },
                { field: 'related_name', title: '关联名称' },
                { field: 'quantity', title: '数量' },
                { 
                    field: 'suggested_disposal', 
                    title: '处置建议',
                    render: (v) => this.getDisposalText(v)
                },
                { field: 'applicant', title: '申请人' },
                { field: 'apply_time', title: '申请时间' },
                { 
                    field: 'current_approval_level', 
                    title: '当前审批',
                    render: (v) => {
                        const level = parseInt(v) || 0;
                        return level === 1 ? '班组长审批' : level === 2 ? '部门主管审批' : '-';
                    }
                },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id) => `
                        <button class="btn btn-sm btn-outline" onclick="DisposalPage.showOrderDetail(${id})">查看</button>
                        <button class="btn btn-sm btn-success" onclick="DisposalPage.showApprovalModal(${id}, 'approve')" style="margin-left: 4px;">通过</button>
                        <button class="btn btn-sm btn-warning" onclick="DisposalPage.showApprovalModal(${id}, 'return')" style="margin-left: 4px;">退回</button>
                        <button class="btn btn-sm btn-danger" onclick="DisposalPage.showApprovalModal(${id}, 'reject')" style="margin-left: 4px;">驳回</button>
                    `
                }
            ],
            data: data
        });
    },

    showApprovalModal(id, action) {
        const actionText = {
            'approve': '通过',
            'return': '退回',
            'reject': '驳回'
        }[action];

        const requireOpinion = action !== 'approve';

        const html = `
            <div style="padding: 20px;">
                <h4 style="margin-bottom: 20px;">审批${actionText}</h4>
                <form id="approvalForm">
                    <div class="form-group">
                        <label>审批意见${requireOpinion ? ' *' : ''}</label>
                        <textarea class="form-control" name="opinion" rows="3" ${requireOpinion ? 'required' : ''} placeholder="请输入审批意见..."></textarea>
                    </div>
                </form>
            </div>
        `;

        Modal.show({
            title: `审批${actionText}`,
            content: html,
            width: 500,
            onConfirm: async () => {
                const form = document.getElementById('approvalForm');
                const formData = new FormData(form);
                const data = {
                    opinion: formData.get('opinion') || ''
                };

                if (requireOpinion && !data.opinion) {
                    Toast.error('请填写审批意见');
                    return;
                }

                try {
                    let res;
                    if (action === 'approve') {
                        res = await DisposalService.approveOrder(id, data);
                    } else if (action === 'return') {
                        res = await DisposalService.returnOrder(id, data);
                    } else if (action === 'reject') {
                        res = await DisposalService.rejectOrder(id, data);
                    }

                    if (res.code === 200) {
                        Toast.success(`已${actionText}`);
                        Modal.close();
                        this.loadPendingApprovals();
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

    renderStatisticsTab(container) {
        const currentMonth = new Date().toISOString().slice(0, 7);
        container.innerHTML = `
            <div class="stat-cards" id="statsCards" style="margin-bottom: 24px;"></div>
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 class="card-title">处置方式分布</h3>
                        <input type="month" class="form-control" id="statsMonth" value="${currentMonth}" style="width: 150px;" onchange="DisposalPage.loadMonthlyStats()">
                    </div>
                    <div class="card-body">
                        <div style="height: 300px;">
                            <canvas id="pieChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 class="card-title">月度处置趋势</h3>
                        <select class="form-control" id="trendMonths" style="width: 120px;" onchange="DisposalPage.loadTrendStats()">
                            <option value="6">近6个月</option>
                            <option value="12">近12个月</option>
                            <option value="3">近3个月</option>
                        </select>
                    </div>
                    <div class="card-body">
                        <div style="height: 300px;">
                            <canvas id="lineChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card" style="margin-top: 24px;">
                <div class="card-header">
                    <h3 class="card-title">月度明细统计</h3>
                </div>
                <div class="card-body">
                    <div id="monthlyStatsTable"></div>
                </div>
            </div>
        `;
    },

    async loadStatistics() {
        await Promise.all([
            this.loadMonthlyStats(),
            this.loadTrendStats()
        ]);
    },

    async loadMonthlyStats() {
        const month = document.getElementById('statsMonth')?.value;
        const [year, monthNum] = month ? month.split('-').map(Number) : [];

        try {
            const res = await DisposalService.getMonthlyStatistics({ year, month: monthNum });
            if (res.code === 200) {
                this.monthlyStats = res.data;
                this.renderStatsCards();
                this.renderPieChart();
                this.renderMonthlyStatsTable();
            }
        } catch (error) {
            Toast.error('加载月度统计失败');
        }
    },

    async loadTrendStats() {
        const months = parseInt(document.getElementById('trendMonths')?.value || '6');
        try {
            const res = await DisposalService.getTrendStatistics({ months });
            if (res.code === 200) {
                this.trendStats = res.data;
                this.renderLineChart();
            }
        } catch (error) {
            Toast.error('加载趋势统计失败');
        }
    },

    renderStatsCards() {
        const container = document.getElementById('statsCards');
        if (!container || !this.monthlyStats) return;

        const stats = this.monthlyStats.statistics;
        const total = this.monthlyStats.total;

        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-card-icon primary">🔄</div>
                <div class="stat-card-title">返工</div>
                <div class="stat-card-value">${stats.rework.count} 单 / ${stats.rework.quantity} 件</div>
                <div style="font-size: 12px; color: #dc3545; margin-top: 4px;">损失: ¥${stats.rework.loss?.toFixed(2) || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-icon success">✅</div>
                <div class="stat-card-title">让步接收</div>
                <div class="stat-card-value">${stats.concession.count} 单 / ${stats.concession.quantity} 件</div>
                <div style="font-size: 12px; color: #dc3545; margin-top: 4px;">损失: ¥${stats.concession.loss?.toFixed(2) || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-icon danger">🗑️</div>
                <div class="stat-card-title">报废</div>
                <div class="stat-card-value">${stats.scrap.count} 单 / ${stats.scrap.quantity} 件</div>
                <div style="font-size: 12px; color: #dc3545; margin-top: 4px;">损失: ¥${stats.scrap.loss?.toFixed(2) || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-icon warning">📊</div>
                <div class="stat-card-title">本月总计</div>
                <div class="stat-card-value">${total.count} 单 / ${total.quantity} 件</div>
                <div style="font-size: 12px; color: #dc3545; margin-top: 4px;">总损失: ¥${total.loss?.toFixed(2) || 0}</div>
            </div>
        `;
    },

    renderPieChart() {
        const canvas = document.getElementById('pieChart');
        if (!canvas || !this.monthlyStats) return;

        if (this.pieChart) {
            this.pieChart.destroy();
        }

        const stats = this.monthlyStats.statistics;
        const data = {
            labels: ['返工', '让步接收', '报废'],
            datasets: [{
                data: [stats.rework.quantity, stats.concession.quantity, stats.scrap.quantity],
                backgroundColor: ['#17a2b8', '#28a745', '#dc3545'],
                borderWidth: 0
            }]
        };

        this.pieChart = new Chart(canvas, {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },

    renderLineChart() {
        const canvas = document.getElementById('lineChart');
        if (!canvas || !this.trendStats) return;

        if (this.lineChart) {
            this.lineChart.destroy();
        }

        const trend = this.trendStats.trend || [];
        const labels = trend.map(t => t.month);
        const reworkData = trend.map(t => t.rework.quantity);
        const concessionData = trend.map(t => t.concession.quantity);
        const scrapData = trend.map(t => t.scrap.quantity);

        this.lineChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '返工',
                        data: reworkData,
                        borderColor: '#17a2b8',
                        backgroundColor: 'rgba(23, 162, 184, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: '让步接收',
                        data: concessionData,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: '报废',
                        data: scrapData,
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    },

    renderMonthlyStatsTable() {
        const container = document.getElementById('monthlyStatsTable');
        if (!container || !this.monthlyStats) return;

        const stats = this.monthlyStats.statistics;
        const total = this.monthlyStats.total;

        new DataTable('#monthlyStatsTable', {
            columns: [
                { field: 'type', title: '处置方式' },
                { field: 'count', title: '单据数' },
                { field: 'quantity', title: '数量(件)' },
                { 
                    field: 'loss', 
                    title: '损失估算(元)',
                    render: (v) => `¥${v?.toFixed(2) || 0}`
                },
                { 
                    field: 'quantity_ratio', 
                    title: '数量占比',
                    render: (v, row) => {
                        const ratio = total.quantity > 0 ? (row.quantity / total.quantity * 100).toFixed(2) : 0;
                        return `${ratio}%`;
                    }
                },
                { 
                    field: 'loss_ratio', 
                    title: '损失占比',
                    render: (v, row) => {
                        const ratio = total.loss > 0 ? (row.loss / total.loss * 100).toFixed(2) : 0;
                        return `${ratio}%`;
                    }
                }
            ],
            data: [
                { type: '返工', ...stats.rework },
                { type: '让步接收', ...stats.concession },
                { type: '报废', ...stats.scrap },
                { type: '合计', ...total, quantity_ratio: 100, loss_ratio: 100 }
            ]
        });
    },

    destroy() {
        if (this.pieChart) {
            this.pieChart.destroy();
            this.pieChart = null;
        }
        if (this.lineChart) {
            this.lineChart.destroy();
            this.lineChart = null;
        }
    }
};

window.DisposalPage = DisposalPage;
