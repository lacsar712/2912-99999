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
        } else if (status === 'completed') {
            buttons.push(`<span class="text-muted">已完成</span>`);
        } else if (status === 'cancelled') {
            buttons.push(`<span class="text-muted">已取消</span>`);
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
    }
};

window.TasksPage = TasksPage;
