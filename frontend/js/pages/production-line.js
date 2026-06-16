/**
 * 生产线管理页面 - 集成任务管理
 */
const ProductionLinePage = {
    lines: [],
    tasks: {},
    expandedLineId: null,

    init() {
        this.loadData();
    },

    async loadData() {
        try {
            // 并行加载生产线和任务
            const [linesRes, tasksRes] = await Promise.all([
                ProductionService.getLines({ size: 100 }),
                ProductionService.getTasks({ size: 200 })
            ]);

            if (linesRes.code === 200) {
                this.lines = linesRes.data.items || [];
            }

            if (tasksRes.code === 200) {
                // 按生产线ID分组任务
                const allTasks = tasksRes.data.items || [];
                this.tasks = {};
                allTasks.forEach(task => {
                    if (!this.tasks[task.line_id]) {
                        this.tasks[task.line_id] = [];
                    }
                    this.tasks[task.line_id].push(task);
                });
            }

            this.renderPage();
        } catch (error) {
            Toast.error('加载数据失败');
            console.error(error);
        }
    },

    renderPage() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 class="card-title" style="margin: 0;">生产线管理</h3>
                    <div>
                        <button class="btn btn-primary" onclick="ProductionLinePage.showAddLineModal()">
                            + 新增生产线
                        </button>
                    </div>
                </div>
                <div class="card-body" style="padding: 0;">
                    ${this.renderLinesTable()}
                </div>
            </div>
        `;
    },

    renderLinesTable() {
        if (!this.lines.length) {
            return `
                <div style="text-align: center; padding: 60px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">🏭</div>
                    <div>暂无生产线数据</div>
                    <button class="btn btn-primary" style="margin-top: 16px;" onclick="ProductionLinePage.showAddLineModal()">
                        新增生产线
                    </button>
                </div>
            `;
        }

        return `
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 40px;"></th>
                        <th>生产线编号</th>
                        <th>生产线名称</th>
                        <th>位置</th>
                        <th>负责人</th>
                        <th>产能</th>
                        <th>状态</th>
                        <th>任务数</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.lines.map(line => this.renderLineRow(line)).join('')}
                </tbody>
            </table>
        `;
    },

    renderLineRow(line) {
        const lineTasks = this.tasks[line.id] || [];
        const isExpanded = this.expandedLineId === line.id;

        return `
            <tr class="line-row" data-line-id="${line.id}">
                <td>
                    <button class="btn btn-sm btn-outline" onclick="ProductionLinePage.toggleTasks(${line.id})" 
                            style="padding: 4px 8px; font-size: 12px;">
                        ${isExpanded ? '▼' : '▶'}
                    </button>
                </td>
                <td>${line.line_code || '-'}</td>
                <td><strong>${line.line_name || '-'}</strong></td>
                <td>${line.location || '-'}</td>
                <td>${line.supervisor || '-'}</td>
                <td>${line.capacity || '-'}</td>
                <td><span class="status-badge ${line.status}">${this.getStatusText(line.status)}</span></td>
                <td>
                    <span class="badge badge-info">${lineTasks.length}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="ProductionLinePage.showAddTaskModal(${line.id}, '${line.line_name}')">
                        + 任务
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="ProductionLinePage.editLine(${line.id})">编辑</button>
                </td>
            </tr>
            ${isExpanded ? this.renderTasksSection(line, lineTasks) : ''}
        `;
    },

    renderTasksSection(line, tasks) {
        return `
            <tr class="tasks-section" data-line-id="${line.id}">
                <td colspan="9" style="background: var(--bg-light); padding: 0;">
                    <div style="padding: 16px; border-top: 2px solid var(--primary-color);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <h4 style="margin: 0; color: var(--primary-color);">
                                📋 ${line.line_name} - 生产任务
                            </h4>
                            <button class="btn btn-sm btn-primary" onclick="ProductionLinePage.showAddTaskModal(${line.id}, '${line.line_name}')">
                                + 新建任务
                            </button>
                        </div>
                        ${tasks.length ? this.renderTasksTable(tasks) : `
                            <div style="text-align: center; padding: 20px; color: var(--text-secondary);">
                                该生产线暂无任务
                            </div>
                        `}
                    </div>
                </td>
            </tr>
        `;
    },

    renderTasksTable(tasks) {
        return `
            <table class="data-table" style="background: white;">
                <thead>
                    <tr>
                        <th>任务编号</th>
                        <th>任务名称</th>
                        <th>产品</th>
                        <th>计划数量</th>
                        <th>完成数量</th>
                        <th>进度</th>
                        <th>优先级</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${tasks.map(task => `
                        <tr>
                            <td>${task.task_code || '-'}</td>
                            <td>${task.task_name || '-'}</td>
                            <td>${task.product_name || '-'} ${task.product_spec || ''}</td>
                            <td>${task.quantity || 0}</td>
                            <td>${task.completed_quantity || 0}</td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <div style="flex: 1; height: 8px; background: var(--border-light); border-radius: 4px; min-width: 60px;">
                                        <div style="width: ${task.progress || 0}%; background: var(--primary-color); height: 100%; border-radius: 4px;"></div>
                                    </div>
                                    <span style="font-size: 12px; min-width: 36px;">${task.progress || 0}%</span>
                                </div>
                            </td>
                            <td>
                                <span class="badge ${task.priority >= 8 ? 'badge-danger' : task.priority >= 5 ? 'badge-warning' : 'badge-success'}">
                                    ${task.priority || 5}
                                </span>
                            </td>
                            <td><span class="status-badge ${task.status}">${this.getTaskStatusText(task.status)}</span></td>
                            <td>
                                ${task.status === 'pending' ? `
                                    <button class="btn btn-sm btn-success" onclick="ProductionLinePage.startTask(${task.id})">开始</button>
                                ` : ''}
                                ${task.status === 'in_progress' ? `
                                    <button class="btn btn-sm btn-warning" onclick="ProductionLinePage.pauseTask(${task.id})">暂停</button>
                                    <button class="btn btn-sm btn-success" onclick="ProductionLinePage.completeTask(${task.id})">完成</button>
                                ` : ''}
                                ${task.status === 'paused' ? `
                                    <button class="btn btn-sm btn-success" onclick="ProductionLinePage.resumeTask(${task.id})">继续</button>
                                ` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },

    getStatusText(status) {
        const map = { running: '运行中', stopped: '已停止', maintenance: '维护中', error: '故障' };
        return map[status] || status;
    },

    getTaskStatusText(status) {
        const map = { pending: '待开始', in_progress: '进行中', paused: '已暂停', completed: '已完成', cancelled: '已取消' };
        return map[status] || status;
    },

    toggleTasks(lineId) {
        this.expandedLineId = this.expandedLineId === lineId ? null : lineId;
        this.renderPage();
    },

    showAddLineModal() {
        new Modal({
            title: '新增生产线',
            content: this.getLineFormHTML(),
            width: '500px',
            onConfirm: () => this.saveLine()
        }).show();
    },

    getLineFormHTML(data = {}) {
        return `
            <form id="lineForm">
                <div class="form-group">
                    <label class="form-label">生产线编号 <span style="color:red;">*</span></label>
                    <input type="text" class="form-control" name="line_code" value="${data.line_code || ''}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">生产线名称 <span style="color:red;">*</span></label>
                    <input type="text" class="form-control" name="line_name" value="${data.line_name || ''}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">位置</label>
                    <input type="text" class="form-control" name="location" value="${data.location || ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">负责人</label>
                    <input type="text" class="form-control" name="supervisor" value="${data.supervisor || ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">产能</label>
                    <input type="number" class="form-control" name="capacity" value="${data.capacity || 0}">
                </div>
            </form>
        `;
    },

    async saveLine(editId = null) {
        const form = document.getElementById('lineForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        if (!data.line_code || !data.line_name) {
            Toast.error('请填写必填项');
            return false;
        }

        try {
            let response;
            if (editId) {
                response = await ProductionService.updateLine(editId, data);
            } else {
                response = await ProductionService.createLine(data);
            }

            if (response.code === 200 || response.code === 201) {
                Toast.success(editId ? '更新成功' : '创建成功');
                this.loadData();
                return true;
            } else {
                Toast.error(response.message);
                return false;
            }
        } catch (error) {
            Toast.error('操作失败');
            return false;
        }
    },

    async editLine(lineId) {
        const line = this.lines.find(l => l.id === lineId);
        if (!line) return;

        new Modal({
            title: '编辑生产线',
            content: this.getLineFormHTML(line),
            width: '500px',
            onConfirm: () => this.saveLine(lineId)
        }).show();
    },

    showAddTaskModal(lineId, lineName) {
        new Modal({
            title: `新建任务 - ${lineName}`,
            content: this.getTaskFormHTML(lineId),
            width: '500px',
            onConfirm: () => this.saveTask()
        }).show();
    },

    getTaskFormHTML(lineId) {
        const taskCode = `TASK-${Date.now().toString().slice(-6)}`;
        return `
            <form id="taskForm">
                <input type="hidden" name="line_id" value="${lineId}">
                <div class="form-group">
                    <label class="form-label">任务编号 <span style="color:red;">*</span></label>
                    <input type="text" class="form-control" name="task_code" value="${taskCode}" required>
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
                    <label class="form-label">产品规格</label>
                    <input type="text" class="form-control" name="product_spec">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div class="form-group">
                        <label class="form-label">计划数量</label>
                        <input type="number" class="form-control" name="quantity" value="1000">
                    </div>
                    <div class="form-group">
                        <label class="form-label">优先级</label>
                        <select class="form-control" name="priority">
                            <option value="5">普通</option>
                            <option value="7">较高</option>
                            <option value="9">紧急</option>
                        </select>
                    </div>
                </div>
            </form>
        `;
    },

    async saveTask() {
        const form = document.getElementById('taskForm');
        const data = Object.fromEntries(new FormData(form));
        data.quantity = parseInt(data.quantity) || 1000;
        data.priority = parseInt(data.priority) || 5;

        try {
            const response = await ProductionService.createTask(data);
            if (response.code === 200 || response.code === 201) {
                Toast.success('任务创建成功');
                this.loadData();
                return true;
            } else {
                Toast.error(response.message);
                return false;
            }
        } catch (error) {
            Toast.error('创建失败');
            return false;
        }
    },

    async startTask(taskId) {
        await this.updateTaskStatus(taskId, 'in_progress', '开始');
    },

    async pauseTask(taskId) {
        await this.updateTaskStatus(taskId, 'paused', '暂停');
    },

    async resumeTask(taskId) {
        await this.updateTaskStatus(taskId, 'in_progress', '继续');
    },

    async completeTask(taskId) {
        await this.updateTaskStatus(taskId, 'completed', '完成');
    },

    async updateTaskStatus(taskId, status, action) {
        try {
            const response = await ProductionService.updateTaskStatus(taskId, status);
            if (response.code === 200) {
                Toast.success(`任务已${action}`);
                this.loadData();
            } else {
                Toast.error(response.message);
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    }
};

window.ProductionLinePage = ProductionLinePage;
