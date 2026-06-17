/**
 * 生产任务页面
 */
const TasksPage = {
    init() {
        this.loadTasks();
    },

    async loadTasks() {
        try {
            const response = await ProductionService.getTasks({ size: 100 });
            if (response.code === 200) {
                this.renderTasks(response.data.items || []);
            }
        } catch (error) {
            Toast.error('加载任务失败');
        }
    },

    renderTasks(tasks) {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">生产任务管理</h3>
                    <button class="btn btn-primary" onclick="TasksPage.showAddModal()">新建任务</button>
                </div>
                <div class="card-body">
                    <div id="taskTable"></div>
                </div>
            </div>
        `;

        new DataTable('#taskTable', {
            columns: [
                { field: 'task_code', title: '任务编号' },
                { field: 'task_name', title: '任务名称' },
                { field: 'product_name', title: '产品' },
                { field: 'quantity', title: '计划数量', render: (v) => v || '-' },
                { field: 'completed_quantity', title: '完成数量', render: (v, row) => `${v || 0} / ${row.quantity || 0}` },
                { field: 'progress', title: '进度', render: (v) => `<div style="width: 100px; background: var(--border-light); height: 8px; border-radius: 4px;"><div style="width: ${v || 0}%; background: var(--primary-color); height: 100%; border-radius: 4px;"></div></div>` },
                { field: 'priority', title: '优先级', render: (v) => `<span class="badge ${v >= 8 ? 'badge-danger' : v >= 5 ? 'badge-warning' : 'badge-success'}">${v}</span>` },
                { field: 'status', title: '状态', render: (v) => `<span class="status-badge ${v}">${this.getStatusText(v)}</span>` },
                { 
                    field: 'id', 
                    title: '操作', 
                    render: (id, row) => this.renderActionButtons(id, row) 
                }
            ],
            data: tasks
        });
    },

    renderActionButtons(id, task) {
        const buttons = [];
        const status = task.status;
        
        buttons.push(`<button class="btn btn-sm btn-outline" onclick="TasksPage.showTaskDetail(${id})">详情</button>`);
        
        if (status === 'pending') {
            buttons.push(`<button class="btn btn-sm btn-success" onclick="TasksPage.startTask(${id})">开始</button>`);
            buttons.push(`<button class="btn btn-sm btn-secondary" onclick="TasksPage.cancelTask(${id})">取消</button>`);
        } else if (status === 'in_progress') {
            buttons.push(`<button class="btn btn-sm btn-warning" onclick="TasksPage.pauseTask(${id})">暂停</button>`);
            buttons.push(`<button class="btn btn-sm btn-success" onclick="TasksPage.completeTask(${id})">完成</button>`);
            buttons.push(`<button class="btn btn-sm btn-secondary" onclick="TasksPage.cancelTask(${id})">取消</button>`);
        } else if (status === 'paused') {
            buttons.push(`<button class="btn btn-sm btn-success" onclick="TasksPage.resumeTask(${id})">继续</button>`);
            buttons.push(`<button class="btn btn-sm btn-secondary" onclick="TasksPage.cancelTask(${id})">取消</button>`);
        }
        
        return buttons.join(' ');
    },

    getStatusText(status) {
        const map = { pending: '待开始', in_progress: '进行中', paused: '已暂停', completed: '已完成', cancelled: '已取消' };
        return map[status] || status;
    },

    async updateTaskStatus(id, status) {
        try {
            const response = await ProductionService.updateTaskStatus(id, status);
            if (response.code === 200) {
                Toast.success('任务状态更新成功');
                this.loadTasks();
                return true;
            } else {
                Toast.error(response.message || '操作失败');
                return false;
            }
        } catch (error) {
            console.error('更新任务状态失败:', error);
            Toast.error('操作失败，请稍后重试');
            return false;
        }
    },

    async startTask(id) {
        if (!confirm('确定要开始此任务吗？')) return;
        await this.updateTaskStatus(id, 'in_progress');
    },

    async pauseTask(id) {
        if (!confirm('确定要暂停此任务吗？')) return;
        await this.updateTaskStatus(id, 'paused');
    },

    async resumeTask(id) {
        if (!confirm('确定要继续此任务吗？')) return;
        await this.updateTaskStatus(id, 'in_progress');
    },

    async completeTask(id) {
        if (!confirm('确定要完成此任务吗？')) return;
        await this.updateTaskStatus(id, 'completed');
    },

    async cancelTask(id) {
        if (!confirm('确定要取消此任务吗？')) return;
        await this.updateTaskStatus(id, 'cancelled');
    },

    showAddModal() {
        new Modal({
            title: '新建生产任务',
            content: `
                <form id="taskForm">
                    <div class="form-group">
                        <label class="form-label">任务编号 <span style="color:red;">*</span></label>
                        <input type="text" class="form-control" name="task_code" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">任务名称 <span style="color:red;">*</span></label>
                        <input type="text" class="form-control" name="task_name" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">产品名称</label>
                        <input type="text" class="form-control" name="product_name">
                    </div>
                    <div class="form-group">
                        <label class="form-label">计划数量</label>
                        <input type="number" class="form-control" name="quantity">
                    </div>
                    <div class="form-group">
                        <label class="form-label">优先级</label>
                        <select class="form-control" name="priority">
                            <option value="5">普通</option>
                            <option value="7">较高</option>
                            <option value="9">紧急</option>
                        </select>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('taskForm');
                const data = Object.fromEntries(new FormData(form));
                data.quantity = parseInt(data.quantity);
                data.priority = parseInt(data.priority);

                const response = await ProductionService.createTask(data);
                if (response.code === 201) {
                    Toast.success('创建成功');
                    TasksPage.loadTasks();
                    return true;
                } else {
                    Toast.error(response.message);
                    return false;
                }
            }
        }).show();
    },

    async showTaskDetail(taskId) {
        try {
            const response = await ProductionService.getTask(taskId);
            if (response.code !== 200) {
                Toast.error('获取任务详情失败');
                return;
            }
            const task = response.data;

            new Modal({
                title: `任务详情 - ${task.task_code}`,
                width: '900px',
                content: `
                    <div class="safety-tab-bar">
                        <div class="safety-tab active" data-detail-tab="basic" onclick="TasksPage.switchDetailTab('basic')">基本信息</div>
                        <div class="safety-tab" data-detail-tab="cost" onclick="TasksPage.switchDetailTab('cost')">成本</div>
                    </div>
                    <div id="detailTabContent"></div>
                `,
                onShow: () => {
                    window.currentTaskId = taskId;
                    TasksPage.switchDetailTab('basic');
                }
            }).show();
        } catch (error) {
            console.error('获取任务详情失败:', error);
            Toast.error('获取任务详情失败');
        }
    },

    switchDetailTab(tab) {
        document.querySelectorAll('[data-detail-tab]').forEach(t => {
            t.classList.toggle('active', t.dataset.detailTab === tab);
        });

        const content = document.getElementById('detailTabContent');
        if (tab === 'basic') {
            this.renderTaskBasicTab(content);
        } else {
            this.renderTaskCostTab(content);
        }
    },

    async renderTaskBasicTab(container) {
        try {
            const response = await ProductionService.getTask(window.currentTaskId);
            if (response.code !== 200) return;
            const task = response.data;

            container.innerHTML = `
                <div style="padding: 20px 0;">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">任务编号</label>
                            <div class="form-control-plaintext">${Validator.sanitize(task.task_code || '-')}</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">任务名称</label>
                            <div class="form-control-plaintext">${Validator.sanitize(task.task_name || '-')}</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">产品</label>
                            <div class="form-control-plaintext">${Validator.sanitize(task.product_name || '-')}</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">生产线</label>
                            <div class="form-control-plaintext">${Validator.sanitize(task.line_name || '-')}</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">计划数量</label>
                            <div class="form-control-plaintext">${task.quantity || 0}</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">完成数量</label>
                            <div class="form-control-plaintext">${task.completed_quantity || 0}</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">进度</label>
                            <div class="form-control-plaintext">${task.progress || 0}%</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">优先级</label>
                            <div class="form-control-plaintext">
                                <span class="badge ${task.priority >= 8 ? 'badge-danger' : task.priority >= 5 ? 'badge-warning' : 'badge-success'}">${task.priority || 0}</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">状态</label>
                            <div class="form-control-plaintext">
                                <span class="status-badge ${task.status}">${this.getStatusText(task.status)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">备注</label>
                        <div class="form-control-plaintext">${Validator.sanitize(task.remark || '-')}</div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('加载任务基本信息失败:', error);
        }
    },

    async renderTaskCostTab(container) {
        container.innerHTML = `
            <div style="padding: 20px 0;">
                <div class="loading-text" style="text-align: center; padding: 40px;">加载中...</div>
            </div>
        `;

        try {
            const taskId = window.currentTaskId;
            const [taskRes, costRes] = await Promise.all([
                ProductionService.getTask(taskId),
                CostService.getTaskCost(taskId)
            ]);

            if (taskRes.code !== 200 || costRes.code !== 200) {
                container.innerHTML = '<div class="text-danger" style="text-align: center; padding: 40px;">加载成本数据失败</div>';
                return;
            }

            const task = taskRes.data;
            const costData = costRes.data;
            const records = costData.records || [];
            const summary = costData.summary || {};
            const typeMap = {
                material: '原材料',
                labor: '人工',
                depreciation: '设备折旧',
                energy: '能源',
                other: '其他'
            };
            const typeColors = {
                material: 'rgba(0, 123, 255, 0.8)',
                labor: 'rgba(40, 167, 69, 0.8)',
                depreciation: 'rgba(23, 162, 184, 0.8)',
                energy: 'rgba(255, 193, 7, 0.8)',
                other: 'rgba(108, 117, 125, 0.8)'
            };

            container.innerHTML = `
                <div style="padding: 20px 0;">
                    ${task.status === 'completed' && !summary.is_calculated ? `
                        <div class="alert alert-warning" style="margin-bottom: 20px;">
                            <strong>提示：</strong>该任务已完成但尚未进行成本初算。
                            <button class="btn btn-sm btn-primary" style="margin-left: 12px;" onclick="TasksPage.calculateTaskCost()">立即计算</button>
                        </div>
                    ` : ''}

                    ${summary.is_calculated ? `
                        <div class="alert alert-info" style="margin-bottom: 20px;">
                            <strong>成本初算状态：</strong>${summary.is_auto ? '自动折算完成' : '手工补录完成'}
                            ${summary.missing_elements && summary.missing_elements.length > 0 ? `
                                <br><span class="text-warning">⚠️ 以下要素数据缺失，请手工补录：${summary.missing_elements.join('、')}</span>
                            ` : ''}
                        </div>
                    ` : ''}

                    <div class="grid grid-2" style="margin-bottom: 20px;">
                        <div class="card" style="box-shadow: none; border: 1px solid var(--border-light); margin-bottom: 0;">
                            <div class="card-header" style="padding: 12px 16px;">
                                <h4 class="card-title" style="font-size: 14px; margin: 0;">成本构成</h4>
                            </div>
                            <div class="card-body" style="padding: 16px;">
                                <canvas id="taskCostPieChart" style="height: 250px;"></canvas>
                            </div>
                        </div>
                        <div class="card" style="box-shadow: none; border: 1px solid var(--border-light); margin-bottom: 0;">
                            <div class="card-header" style="padding: 12px 16px;">
                                <h4 class="card-title" style="font-size: 14px; margin: 0;">成本汇总</h4>
                            </div>
                            <div class="card-body" style="padding: 16px;">
                                <div style="text-align: center; margin-bottom: 20px;">
                                    <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">总成本</div>
                                    <div style="font-size: 36px; font-weight: bold; color: var(--primary-color);">¥${Formatter.formatNumber(summary.total_amount || 0)}</div>
                                    ${task.completed_quantity > 0 ? `
                                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                                            单位成本：¥${Formatter.formatNumber((summary.total_amount || 0) / task.completed_quantity)} / 件
                                        </div>
                                    ` : ''}
                                </div>
                                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                                    <div style="padding: 12px; background: var(--bg-light); border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: var(--text-secondary);">原材料</div>
                                        <div style="font-size: 18px; font-weight: bold; color: #007bff;">¥${Formatter.formatNumber(summary.material_amount || 0)}</div>
                                    </div>
                                    <div style="padding: 12px; background: var(--bg-light); border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: var(--text-secondary);">人工</div>
                                        <div style="font-size: 18px; font-weight: bold; color: #28a745;">¥${Formatter.formatNumber(summary.labor_amount || 0)}</div>
                                    </div>
                                    <div style="padding: 12px; background: var(--bg-light); border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: var(--text-secondary);">设备折旧</div>
                                        <div style="font-size: 18px; font-weight: bold; color: #17a2b8;">¥${Formatter.formatNumber(summary.depreciation_amount || 0)}</div>
                                    </div>
                                    <div style="padding: 12px; background: var(--bg-light); border-radius: 8px; text-align: center;">
                                        <div style="font-size: 12px; color: var(--text-secondary);">能源</div>
                                        <div style="font-size: 18px; font-weight: bold; color: #ffc107;">¥${Formatter.formatNumber(summary.energy_amount || 0)}</div>
                                    </div>
                                    <div style="padding: 12px; background: var(--bg-light); border-radius: 8px; text-align: center; grid-column: span 2;">
                                        <div style="font-size: 12px; color: var(--text-secondary);">其他</div>
                                        <div style="font-size: 18px; font-weight: bold; color: #6c757d;">¥${Formatter.formatNumber(summary.other_amount || 0)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card" style="box-shadow: none; border: 1px solid var(--border-light);">
                        <div class="card-header" style="padding: 12px 16px;">
                            <h4 class="card-title" style="font-size: 14px; margin: 0;">成本明细</h4>
                        </div>
                        <div class="card-body" style="padding: 0;">
                            ${records.length > 0 ? `
                                <table class="table table-hover" style="margin-bottom: 0;">
                                    <thead>
                                        <tr style="background: var(--bg-light);">
                                            <th>登记编号</th>
                                            <th>成本要素</th>
                                            <th>类型</th>
                                            <th>数量</th>
                                            <th>单价(元)</th>
                                            <th>金额(元)</th>
                                            <th>来源</th>
                                            <th>登记人</th>
                                            <th>登记日期</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${records.map(r => `
                                            <tr>
                                                <td>${Validator.sanitize(r.record_code || '-')}</td>
                                                <td>${Validator.sanitize(r.element_name || '-')}</td>
                                                <td><span class="badge ${r.element_type === 'material' ? 'badge-primary' : r.element_type === 'labor' ? 'badge-success' : r.element_type === 'depreciation' ? 'badge-info' : r.element_type === 'energy' ? 'badge-warning' : 'badge-secondary'}">${typeMap[r.element_type] || r.element_type}</span></td>
                                                <td>${r.quantity || 0} ${r.unit || ''}</td>
                                                <td>${Formatter.formatNumber(r.unit_price || 0)}</td>
                                                <td><strong>¥${Formatter.formatNumber(r.amount || 0)}</strong></td>
                                                <td>${r.source === 'auto' ? '<span class="badge badge-info">自动折算</span>' : '<span class="badge badge-secondary">手工录入</span>'}</td>
                                                <td>${Validator.sanitize(r.register_by || '-')}</td>
                                                <td>${r.record_date || '-'}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            ` : '<div style="text-align: center; padding: 40px; color: var(--text-muted);">暂无成本记录</div>'}
                        </div>
                    </div>
                </div>
            `;

            const pieData = {
                material: summary.material_amount || 0,
                labor: summary.labor_amount || 0,
                depreciation: summary.depreciation_amount || 0,
                energy: summary.energy_amount || 0,
                other: summary.other_amount || 0
            };

            const labels = [];
            const values = [];
            const colors = [];
            Object.entries(pieData).forEach(([type, value]) => {
                if (value > 0) {
                    labels.push(typeMap[type]);
                    values.push(value);
                    colors.push(typeColors[type]);
                }
            });

            if (values.length > 0 && values.some(v => v > 0)) {
                const ctx = document.getElementById('taskCostPieChart');
                if (ctx) {
                    new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: labels,
                            datasets: [{
                                data: values,
                                backgroundColor: colors,
                                borderWidth: 2,
                                borderColor: '#fff'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                            const percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                                            return context.label + ': ¥' + Formatter.formatNumber(context.raw) + ' (' + percentage + '%)';
                                        }
                                    }
                                }
                            }
                        }
                    });
                }
            } else {
                const pieContainer = document.getElementById('taskCostPieChart');
                if (pieContainer) {
                    pieContainer.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">暂无成本数据</div>';
                }
            }
        } catch (error) {
            console.error('加载任务成本数据失败:', error);
            container.innerHTML = '<div class="text-danger" style="text-align: center; padding: 40px;">加载成本数据失败</div>';
        }
    },

    async calculateTaskCost() {
        if (!confirm('确定要计算此任务的成本吗？这将根据生产记录自动折算各项成本。')) return;

        try {
            const response = await CostService.calculateTaskCost(window.currentTaskId);
            if (response.code === 200) {
                Toast.success('成本计算成功');
                this.renderTaskCostTab(document.getElementById('detailTabContent'));
            } else {
                Toast.error(response.message || '计算失败');
            }
        } catch (error) {
            console.error('计算成本失败:', error);
            Toast.error('计算失败，请稍后重试');
        }
    },

    async completeTask(id) {
        if (!confirm('确定要完成此任务吗？系统将自动进行成本初算。')) return;
        const success = await this.updateTaskStatus(id, 'completed');
        if (success) {
            setTimeout(() => {
                Toast.info('任务已完成，系统正在自动计算成本...');
            }, 500);
        }
    }
};

window.TasksPage = TasksPage;
