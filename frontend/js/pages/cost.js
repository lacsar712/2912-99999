/**
 * 成本核算页面 - 成本登记
 */
const CostPage = {
    currentTab: 'records',
    elements: [],
    tasks: [],
    chart: null,
    pieChart: null,

    init() {
        this.loadData();
    },

    async loadData() {
        try {
            const [elementsRes, tasksRes, recordsRes] = await Promise.all([
                CostService.getAllElements(),
                ProductionService.getTasks({ size: 100 }),
                CostService.getRecords({ size: 50 })
            ]);

            if (elementsRes.code === 200) {
                this.elements = elementsRes.data || [];
            }
            if (tasksRes.code === 200) {
                this.tasks = tasksRes.data.items || [];
            }

            this.render();
            if (recordsRes.code === 200) {
                this.renderRecords(recordsRes.data.items || []);
            }
        } catch (error) {
            console.error('加载成本数据失败:', error);
            Toast.error('加载数据失败');
        }
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="cost-page">
                <div class="safety-tab-bar">
                    <div class="safety-tab active" data-tab="records" onclick="CostPage.switchTab('records')">
                        成本登记
                    </div>
                    <div class="safety-tab" data-tab="report" onclick="CostPage.switchTab('report')">
                        成本报表
                    </div>
                </div>

                <div id="tabContent"></div>
            </div>
        `;

        this.switchTab('records');
    },

    switchTab(tab) {
        this.currentTab = tab;
        document.querySelectorAll('.safety-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });

        const tabContent = document.getElementById('tabContent');
        if (tab === 'records') {
            this.renderRecordsTab(tabContent);
        } else {
            this.renderReportTab(tabContent);
        }
    },

    renderRecordsTab(container) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">成本登记列表</h3>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-outline" onclick="CostPage.showElementManager()">
                            管理成本要素
                        </button>
                        <button class="btn btn-primary" onclick="CostPage.showAddModal()">
                            + 新增成本登记
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-toolbar toolbar-filters">
                        <select id="filterTask" class="form-control" style="width: 200px;" onchange="CostPage.filterRecords()">
                            <option value="">全部任务</option>
                            ${this.tasks.map(t => `<option value="${t.id}">${t.task_name}</option>`).join('')}
                        </select>
                        <select id="filterType" class="form-control" style="width: 150px;" onchange="CostPage.filterRecords()">
                            <option value="">全部类型</option>
                            <option value="material">原材料</option>
                            <option value="labor">人工</option>
                            <option value="depreciation">设备折旧</option>
                            <option value="energy">能源</option>
                            <option value="other">其他</option>
                        </select>
                        <input type="date" id="filterStartDate" class="form-control" style="width: 150px;" onchange="CostPage.filterRecords()">
                        <span style="color: var(--text-secondary);">至</span>
                        <input type="date" id="filterEndDate" class="form-control" style="width: 150px;" onchange="CostPage.filterRecords()">
                        <button class="btn btn-outline" onclick="CostPage.resetFilters()">重置</button>
                    </div>
                    <div id="recordsTable"></div>
                </div>
            </div>
        `;
    },

    async renderRecords(records) {
        const tableContainer = document.getElementById('recordsTable');
        if (!tableContainer) return;

        const typeMap = {
            material: '原材料',
            labor: '人工',
            depreciation: '设备折旧',
            energy: '能源',
            other: '其他'
        };

        const typeColors = {
            material: 'badge-primary',
            labor: 'badge-success',
            depreciation: 'badge-info',
            energy: 'badge-warning',
            other: 'badge-secondary'
        };

        new DataTable('#recordsTable', {
            columns: [
                { field: 'record_code', title: '登记编号' },
                { field: 'task_name', title: '生产任务', render: (v) => v || '-' },
                { field: 'element_name', title: '成本要素' },
                { 
                    field: 'element_type', 
                    title: '要素类型', 
                    render: (v) => `<span class="badge ${typeColors[v] || 'badge-secondary'}">${typeMap[v] || v}</span>` 
                },
                { field: 'quantity', title: '数量', render: (v, row) => `${v || 0} ${row.unit || ''}` },
                { field: 'unit_price', title: '单价(元)', render: (v) => Formatter.formatNumber(v || 0) },
                { field: 'amount', title: '金额(元)', render: (v) => `<strong>¥${Formatter.formatNumber(v || 0)}</strong>` },
                { field: 'register_by', title: '登记人' },
                { field: 'record_date', title: '登记日期' },
                { 
                    field: 'source', 
                    title: '来源', 
                    render: (v) => v === 'auto' 
                        ? '<span class="badge badge-info">自动折算</span>' 
                        : '<span class="badge badge-secondary">手工录入</span>' 
                },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id, row) => row.source === 'auto' 
                        ? '<span class="text-muted">自动记录</span>'
                        : `
                            <button class="btn btn-sm btn-outline" onclick="CostPage.editRecord(${id})">编辑</button>
                            <button class="btn btn-sm btn-danger" onclick="CostPage.deleteRecord(${id})">删除</button>
                        `
                }
            ],
            data: records
        });
    },

    async filterRecords() {
        const params = {
            size: 50,
            taskId: document.getElementById('filterTask')?.value || null,
            elementType: document.getElementById('filterType')?.value || null,
            startDate: document.getElementById('filterStartDate')?.value || null,
            endDate: document.getElementById('filterEndDate')?.value || null
        };

        try {
            const response = await CostService.getRecords(params);
            if (response.code === 200) {
                this.renderRecords(response.data.items || []);
            }
        } catch (error) {
            console.error('筛选失败:', error);
        }
    },

    resetFilters() {
        document.getElementById('filterTask').value = '';
        document.getElementById('filterType').value = '';
        document.getElementById('filterStartDate').value = '';
        document.getElementById('filterEndDate').value = '';
        this.filterRecords();
    },

    showAddModal() {
        const today = new Date().toISOString().split('T')[0];
        new Modal({
            title: '新增成本登记',
            width: '800px',
            content: `
                <form id="costForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">关联任务 <span style="color:red;">*</span></label>
                            <select class="form-control" name="task_id" required>
                                <option value="">请选择任务</option>
                                ${this.tasks.filter(t => t.status !== 'cancelled').map(t => 
                                    `<option value="${t.id}">${t.task_code} - ${t.task_name}</option>`
                                ).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">登记日期</label>
                            <input type="date" class="form-control" name="record_date" value="${today}">
                        </div>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <label class="form-label" style="margin: 0;">成本要素明细</label>
                            <button type="button" class="btn btn-sm btn-outline" onclick="CostPage.addElementRow()">
                                + 添加行
                            </button>
                        </div>
                        <div id="elementRows" style="border: 1px solid var(--border-light); border-radius: 8px; padding: 12px; background: var(--bg-light);">
                            ${this.getElementRowHtml(0)}
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">备注</label>
                        <textarea class="form-control" name="remark" rows="2" placeholder="可选"></textarea>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                return await this.submitRecords();
            }
        }).show();
    },

    getElementRowHtml(index) {
        const typeMap = {
            material: '原材料',
            labor: '人工',
            depreciation: '设备折旧',
            energy: '能源',
            other: '其他'
        };

        return `
            <div class="element-row" data-index="${index}" style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 40px; gap: 8px; margin-bottom: 8px; align-items: end;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">成本要素</label>
                    <select class="form-control element-select" name="element_id" required onchange="CostPage.updateElementPrice(this)">
                        <option value="">请选择</option>
                        ${this.elements.map(e => 
                            `<option value="${e.id}" data-price="${e.price}" data-unit="${e.unit}" data-type="${e.element_type}">
                                ${e.element_name} (${typeMap[e.element_type]})
                            </option>`
                        ).join('')}
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">数量</label>
                    <input type="number" class="form-control quantity-input" name="quantity" step="0.01" min="0" required oninput="CostPage.calculateRowAmount(this)">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">单价(元)</label>
                    <input type="number" class="form-control price-input" name="unit_price" step="0.01" min="0" required oninput="CostPage.calculateRowAmount(this)">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">金额(元)</label>
                    <input type="number" class="form-control amount-input" name="amount" step="0.01" min="0" required oninput="CostPage.calculateRowAmount(this)">
                </div>
                ${index > 0 ? `
                    <button type="button" class="btn btn-sm btn-danger" style="margin-bottom: 0;" onclick="CostPage.removeElementRow(this)">
                        ×
                    </button>
                ` : '<div></div>'}
            </div>
        `;
    },

    addElementRow() {
        const container = document.getElementById('elementRows');
        const rows = container.querySelectorAll('.element-row');
        const newIndex = rows.length;
        const newRow = document.createElement('div');
        newRow.innerHTML = this.getElementRowHtml(newIndex);
        container.appendChild(newRow.firstElementChild);
    },

    removeElementRow(btn) {
        btn.closest('.element-row').remove();
    },

    updateElementPrice(select) {
        const row = select.closest('.element-row');
        const option = select.options[select.selectedIndex];
        const price = option.dataset.price || 0;
        const priceInput = row.querySelector('.price-input');
        priceInput.value = price;
        this.calculateRowAmount(priceInput);
    },

    calculateRowAmount(input) {
        const row = input.closest('.element-row');
        const quantity = parseFloat(row.querySelector('.quantity-input').value) || 0;
        const price = parseFloat(row.querySelector('.price-input').value) || 0;
        const amountInput = row.querySelector('.amount-input');
        
        if (input !== amountInput) {
            amountInput.value = (quantity * price).toFixed(2);
        }
    },

    async submitRecords() {
        const form = document.getElementById('costForm');
        const formData = new FormData(form);
        
        const taskId = formData.get('task_id');
        const recordDate = formData.get('record_date');
        const remark = formData.get('remark');

        if (!taskId) {
            Toast.error('请选择关联任务');
            return false;
        }

        const rows = document.querySelectorAll('.element-row');
        const records = [];

        for (const row of rows) {
            const elementId = row.querySelector('[name="element_id"]').value;
            const quantity = parseFloat(row.querySelector('[name="quantity"]').value) || 0;
            const unitPrice = parseFloat(row.querySelector('[name="unit_price"]').value) || 0;
            const amount = parseFloat(row.querySelector('[name="amount"]').value) || 0;

            if (!elementId) {
                Toast.error('请选择成本要素');
                return false;
            }
            if (amount <= 0) {
                Toast.error('金额必须大于0');
                return false;
            }

            records.push({
                element_id: parseInt(elementId),
                quantity: quantity,
                unit_price: unitPrice,
                amount: amount,
                remark: remark,
                record_date: recordDate,
                source: 'manual'
            });
        }

        if (records.length === 0) {
            Toast.error('请至少添加一条成本记录');
            return false;
        }

        try {
            const response = await CostService.batchCreateRecords({
                task_id: parseInt(taskId),
                records: records
            });

            if (response.code === 201) {
                Toast.success('成本登记成功');
                this.loadData();
                return true;
            } else {
                Toast.error(response.message || '登记失败');
                return false;
            }
        } catch (error) {
            console.error('登记失败:', error);
            Toast.error('登记失败，请稍后重试');
            return false;
        }
    },

    async editRecord(recordId) {
        try {
            const response = await CostService.getRecordById(recordId);
            if (response.code !== 200) {
                Toast.error('获取记录失败');
                return;
            }

            const record = response.data;
            new Modal({
                title: '编辑成本登记',
                content: `
                    <form id="editCostForm">
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">成本要素</label>
                                <select class="form-control" name="element_id" required onchange="CostPage.updateEditPrice(this)">
                                    ${this.elements.map(e => 
                                        `<option value="${e.id}" data-price="${e.price}" ${e.id === record.element_id ? 'selected' : ''}>
                                            ${e.element_name}
                                        </option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">登记日期</label>
                                <input type="date" class="form-control" name="record_date" value="${record.record_date || ''}">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">数量 (${record.unit || ''})</label>
                                <input type="number" class="form-control" id="editQuantity" name="quantity" step="0.01" min="0" value="${record.quantity}" oninput="CostPage.calculateEditAmount()">
                            </div>
                            <div class="form-group">
                                <label class="form-label">单价(元)</label>
                                <input type="number" class="form-control" id="editPrice" name="unit_price" step="0.01" min="0" value="${record.unit_price}" oninput="CostPage.calculateEditAmount()">
                            </div>
                            <div class="form-group">
                                <label class="form-label">金额(元)</label>
                                <input type="number" class="form-control" id="editAmount" name="amount" step="0.01" min="0" value="${record.amount}" oninput="CostPage.calculateEditAmount()">
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">备注</label>
                            <textarea class="form-control" name="remark" rows="2">${record.remark || ''}</textarea>
                        </div>
                    </form>
                `,
                onConfirm: async () => {
                    const form = document.getElementById('editCostForm');
                    const data = {
                        element_id: parseInt(form.element_id.value),
                        quantity: parseFloat(form.quantity.value) || 0,
                        unit_price: parseFloat(form.unit_price.value) || 0,
                        amount: parseFloat(form.amount.value) || 0,
                        remark: form.remark.value,
                        record_date: form.record_date.value
                    };

                    try {
                        const updateRes = await CostService.updateRecord(recordId, data);
                        if (updateRes.code === 200) {
                            Toast.success('更新成功');
                            this.loadData();
                            return true;
                        } else {
                            Toast.error(updateRes.message || '更新失败');
                            return false;
                        }
                    } catch (error) {
                        console.error('更新失败:', error);
                        Toast.error('更新失败');
                        return false;
                    }
                }
            }).show();
        } catch (error) {
            console.error('获取记录失败:', error);
        }
    },

    updateEditPrice(select) {
        const option = select.options[select.selectedIndex];
        const price = option.dataset.price || 0;
        document.getElementById('editPrice').value = price;
        this.calculateEditAmount();
    },

    calculateEditAmount() {
        const quantity = parseFloat(document.getElementById('editQuantity').value) || 0;
        const price = parseFloat(document.getElementById('editPrice').value) || 0;
        document.getElementById('editAmount').value = (quantity * price).toFixed(2);
    },

    async deleteRecord(recordId) {
        if (!confirm('确定要删除这条成本记录吗？')) return;

        try {
            const response = await CostService.deleteRecord(recordId);
            if (response.code === 200) {
                Toast.success('删除成功');
                this.loadData();
            } else {
                Toast.error(response.message || '删除失败');
            }
        } catch (error) {
            console.error('删除失败:', error);
            Toast.error('删除失败');
        }
    },

    async showElementManager() {
        const typeMap = {
            material: '原材料',
            labor: '人工',
            depreciation: '设备折旧',
            energy: '能源',
            other: '其他'
        };

        new Modal({
            title: '成本要素管理',
            width: '900px',
            content: `
                <div style="margin-bottom: 16px; display: flex; justify-content: flex-end;">
                    <button class="btn btn-primary btn-sm" onclick="CostPage.showAddElementModal()">+ 新增要素</button>
                </div>
                <div id="elementManagerTable"></div>
            `,
            onShow: async () => {
                const tableContainer = document.getElementById('elementManagerTable');
                new DataTable('#elementManagerTable', {
                    columns: [
                        { field: 'element_code', title: '要素编码' },
                        { field: 'element_name', title: '要素名称' },
                        { field: 'element_type', title: '类型', render: (v) => typeMap[v] || v },
                        { field: 'unit', title: '单位' },
                        { field: 'price', title: '单价(元)', render: (v) => Formatter.formatNumber(v || 0) },
                        { field: 'sort_order', title: '排序' },
                        { 
                            field: 'id', 
                            title: '操作', 
                            render: (id) => `
                                <button class="btn btn-sm btn-outline" onclick="CostPage.editElement(${id})">编辑</button>
                                <button class="btn btn-sm btn-danger" onclick="CostPage.deleteElement(${id})">删除</button>
                            `
                        }
                    ],
                    data: this.elements
                });
            }
        }).show();
    },

    showAddElementModal() {
        new Modal({
            title: '新增成本要素',
            content: `
                <form id="elementForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">要素编码 <span style="color:red;">*</span></label>
                            <input type="text" class="form-control" name="element_code" required placeholder="如: MAT005">
                        </div>
                        <div class="form-group">
                            <label class="form-label">要素名称 <span style="color:red;">*</span></label>
                            <input type="text" class="form-control" name="element_name" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">要素类型 <span style="color:red;">*</span></label>
                            <select class="form-control" name="element_type" required>
                                <option value="material">原材料</option>
                                <option value="labor">人工</option>
                                <option value="depreciation">设备折旧</option>
                                <option value="energy">能源</option>
                                <option value="other">其他</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">计量单位</label>
                            <input type="text" class="form-control" name="unit" placeholder="如: kg, 小时, kWh">
                        </div>
                        <div class="form-group">
                            <label class="form-label">单价(元)</label>
                            <input type="number" class="form-control" name="price" step="0.01" min="0" value="0">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">排序</label>
                            <input type="number" class="form-control" name="sort_order" value="0">
                        </div>
                        <div class="form-group" style="flex: 2;">
                            <label class="form-label">描述</label>
                            <input type="text" class="form-control" name="description">
                        </div>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('elementForm');
                const data = {
                    element_code: form.element_code.value,
                    element_name: form.element_name.value,
                    element_type: form.element_type.value,
                    unit: form.unit.value,
                    price: parseFloat(form.price.value) || 0,
                    sort_order: parseInt(form.sort_order.value) || 0,
                    description: form.description.value
                };

                try {
                    const response = await CostService.createElement(data);
                    if (response.code === 201) {
                        Toast.success('创建成功');
                        this.loadData();
                        return true;
                    } else {
                        Toast.error(response.message || '创建失败');
                        return false;
                    }
                } catch (error) {
                    Toast.error('创建失败');
                    return false;
                }
            }
        }).show();
    },

    async editElement(elementId) {
        const element = this.elements.find(e => e.id === elementId);
        if (!element) return;

        new Modal({
            title: '编辑成本要素',
            content: `
                <form id="editElementForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">要素编码 <span style="color:red;">*</span></label>
                            <input type="text" class="form-control" name="element_code" value="${element.element_code}" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">要素名称 <span style="color:red;">*</span></label>
                            <input type="text" class="form-control" name="element_name" value="${element.element_name}" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">要素类型 <span style="color:red;">*</span></label>
                            <select class="form-control" name="element_type" required>
                                <option value="material" ${element.element_type === 'material' ? 'selected' : ''}>原材料</option>
                                <option value="labor" ${element.element_type === 'labor' ? 'selected' : ''}>人工</option>
                                <option value="depreciation" ${element.element_type === 'depreciation' ? 'selected' : ''}>设备折旧</option>
                                <option value="energy" ${element.element_type === 'energy' ? 'selected' : ''}>能源</option>
                                <option value="other" ${element.element_type === 'other' ? 'selected' : ''}>其他</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">计量单位</label>
                            <input type="text" class="form-control" name="unit" value="${element.unit || ''}">
                        </div>
                        <div class="form-group">
                            <label class="form-label">单价(元)</label>
                            <input type="number" class="form-control" name="price" step="0.01" min="0" value="${element.price || 0}">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">排序</label>
                            <input type="number" class="form-control" name="sort_order" value="${element.sort_order || 0}">
                        </div>
                        <div class="form-group" style="flex: 2;">
                            <label class="form-label">描述</label>
                            <input type="text" class="form-control" name="description" value="${element.description || ''}">
                        </div>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('editElementForm');
                const data = {
                    element_code: form.element_code.value,
                    element_name: form.element_name.value,
                    element_type: form.element_type.value,
                    unit: form.unit.value,
                    price: parseFloat(form.price.value) || 0,
                    sort_order: parseInt(form.sort_order.value) || 0,
                    description: form.description.value
                };

                try {
                    const response = await CostService.updateElement(elementId, data);
                    if (response.code === 200) {
                        Toast.success('更新成功');
                        this.loadData();
                        return true;
                    } else {
                        Toast.error(response.message || '更新失败');
                        return false;
                    }
                } catch (error) {
                    Toast.error('更新失败');
                    return false;
                }
            }
        }).show();
    },

    async deleteElement(elementId) {
        if (!confirm('确定要删除这个成本要素吗？')) return;

        try {
            const response = await CostService.deleteElement(elementId);
            if (response.code === 200) {
                Toast.success('删除成功');
                this.loadData();
            } else {
                Toast.error(response.message || '删除失败');
            }
        } catch (error) {
            Toast.error('删除失败');
        }
    },

    renderReportTab(container) {
        CostReportPage.render(container);
    },

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        if (this.pieChart) {
            this.pieChart.destroy();
            this.pieChart = null;
        }
    }
};

window.CostPage = CostPage;
