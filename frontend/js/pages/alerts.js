/**
 * 告警中心页面
 */
const AlertsPage = {
    statistics: null,
    alerts: [],

    init() {
        this.render();  // 先渲染页面结构
        this.loadStatistics();
        this.loadAlerts();
        this.setupEventListeners();
    },

    async loadStatistics() {
        try {
            const response = await AlertService.getStatistics();
            if (response.code === 200) {
                this.statistics = response.data;
                this.renderStatistics();
            }
        } catch (error) {
            console.error('加载告警统计失败:', error);
        }
    },

    async loadAlerts(page = 1) {
        try {
            const response = await AlertService.getAlerts({ page, size: 20 });
            if (response.code === 200) {
                this.alerts = response.data.items || [];
                this.renderTable();
            }
        } catch (error) {
            Toast.error('加载告警列表失败');
        }
    },

    renderStatistics() {
        const stats = this.statistics || {};
        const severity = stats.by_severity || {};

        // 更新统计卡片
        const cards = document.querySelectorAll('.stat-card-value');
        if (cards.length >= 4) {
            cards[0].textContent = severity.critical || 0;
            cards[1].textContent = (severity.error || 0) + (severity.warning || 0);
            cards[2].textContent = severity.info || 0;
            cards[3].textContent = stats.resolved || 0;
        }
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">告警中心</h3>
                </div>
                <div class="card-body">
                    <div class="grid grid-4" style="margin-bottom: 24px;">
                        <div class="stat-card" style="background: rgba(220,53,69,0.1);">
                            <div class="stat-card-title" style="color: var(--danger-color);">紧急告警</div>
                            <div class="stat-card-value" style="color: var(--danger-color);">0</div>
                        </div>
                        <div class="stat-card" style="background: rgba(255,193,7,0.1);">
                            <div class="stat-card-title" style="color: #856404;">警告</div>
                            <div class="stat-card-value" style="color: #856404;">0</div>
                        </div>
                        <div class="stat-card" style="background: rgba(23,162,184,0.1);">
                            <div class="stat-card-title" style="color: var(--info-color);">提示</div>
                            <div class="stat-card-value" style="color: var(--info-color);">0</div>
                        </div>
                        <div class="stat-card" style="background: rgba(40,167,69,0.1);">
                            <div class="stat-card-title" style="color: var(--success-color);">已解决</div>
                            <div class="stat-card-value" style="color: var(--success-color);">0</div>
                        </div>
                    </div>

                    <div class="toolbar">
                        <div class="toolbar-left">
                            <select class="form-control" id="statusFilter" style="width: 120px;">
                                <option value="">全部状态</option>
                                <option value="active">活动</option>
                                <option value="acknowledged">已确认</option>
                                <option value="resolved">已解决</option>
                            </select>
                            <select class="form-control" id="severityFilter" style="width: 120px; margin-left: 8px;">
                                <option value="">全部级别</option>
                                <option value="critical">紧急</option>
                                <option value="error">错误</option>
                                <option value="warning">警告</option>
                                <option value="info">提示</option>
                            </select>
                        </div>
                        <div class="toolbar-right">
                            <button class="btn btn-primary" id="batchResolveBtn">
                                批量解决
                            </button>
                        </div>
                    </div>

                    <div id="alertsTable"></div>
                </div>
            </div>
        `;
    },

    renderTable() {
        const tableContainer = document.getElementById('alertsTable');
        
        if (!this.alerts || this.alerts.length === 0) {
            tableContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">🔔</div>
                    <div>暂无告警数据</div>
                </div>
            `;
            return;
        }

        const rows = this.alerts.map(alert => this.renderRow(alert)).join('');
        tableContainer.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th><input type="checkbox" id="selectAll"></th>
                        <th>告警编号</th>
                        <th>类型</th>
                        <th>设备</th>
                        <th>消息</th>
                        <th>严重程度</th>
                        <th>状态</th>
                        <th>时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    },

    renderRow(alert) {
        const severityMap = {
            critical: { text: '紧急', class: 'badge-danger' },
            error: { text: '错误', class: 'badge-danger' },
            warning: { text: '警告', class: 'badge-warning' },
            info: { text: '提示', class: 'badge-info' }
        };
        const statusMap = {
            active: { text: '活动', class: 'badge-danger' },
            acknowledged: { text: '已确认', class: 'badge-warning' },
            resolved: { text: '已解决', class: 'badge-success' }
        };

        const severity = severityMap[alert.severity] || { text: alert.severity, class: '' };
        const status = statusMap[alert.status] || { text: alert.status, class: '' };

        return `
            <tr>
                <td><input type="checkbox" class="alert-checkbox" data-id="${alert.id}"></td>
                <td>${alert.alert_code || '-'}</td>
                <td>${alert.alert_type || '-'}</td>
                <td>${alert.equipment_name || alert.equipment_code || '-'}</td>
                <td>${alert.message || '-'}</td>
                <td><span class="badge ${severity.class}">${severity.text}</span></td>
                <td><span class="badge ${status.class}">${status.text}</span></td>
                <td>${this.formatTime(alert.create_time)}</td>
                <td>
                    ${alert.status === 'active' ? `
                        <button class="btn btn-sm btn-warning" onclick="AlertsPage.acknowledge(${alert.id})">确认</button>
                        <button class="btn btn-sm btn-success" onclick="AlertsPage.resolve(${alert.id})">解决</button>
                    ` : ''}
                    ${alert.status === 'acknowledged' ? `
                        <button class="btn btn-sm btn-success" onclick="AlertsPage.resolve(${alert.id})">解决</button>
                    ` : ''}
                </td>
            </tr>
        `;
    },

    formatTime(timeStr) {
        if (!timeStr) return '-';
        try {
            const date = new Date(timeStr);
            return date.toLocaleString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return timeStr;
        }
    },

    setupEventListeners() {
        // 状态筛选
        document.getElementById('statusFilter')?.addEventListener('change', (e) => {
            this.filterAlerts();
        });

        // 严重程度筛选
        document.getElementById('severityFilter')?.addEventListener('change', (e) => {
            this.filterAlerts();
        });

        // 全选
        document.getElementById('selectAll')?.addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.alert-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
        });

        // 批量解决
        document.getElementById('batchResolveBtn')?.addEventListener('click', () => {
            this.batchResolve();
        });
    },

    async filterAlerts() {
        const status = document.getElementById('statusFilter')?.value;
        const severity = document.getElementById('severityFilter')?.value;

        try {
            const response = await AlertService.getAlerts({
                status: status || undefined,
                severity: severity || undefined,
                size: 100
            });
            if (response.code === 200) {
                this.alerts = response.data.items || [];
                this.renderTable();
            }
        } catch (error) {
            Toast.error('筛选失败');
        }
    },

    async acknowledge(alertId) {
        try {
            const response = await AlertService.acknowledgeAlert(alertId);
            if (response.code === 200) {
                Toast.show('告警已确认', 'success');
                this.loadStatistics();
                this.loadAlerts();
            } else {
                Toast.show(response.message, 'error');
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    },

    async resolve(alertId) {
        try {
            const response = await AlertService.resolveAlert(alertId);
            if (response.code === 200) {
                Toast.show('告警已解决', 'success');
                this.loadStatistics();
                this.loadAlerts();
            } else {
                Toast.show(response.message, 'error');
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    },

    async batchResolve() {
        const checkboxes = document.querySelectorAll('.alert-checkbox:checked');
        const ids = Array.from(checkboxes).map(cb => parseInt(cb.dataset.id));

        if (ids.length === 0) {
            Toast.show('请选择要解决的告警', 'warning');
            return;
        }

        try {
            const response = await AlertService.batchResolve(ids);
            if (response.code === 200) {
                Toast.show(`已解决 ${response.data.resolved_count} 条告警`, 'success');
                this.loadStatistics();
                this.loadAlerts();
            } else {
                Toast.show(response.message, 'error');
            }
        } catch (error) {
            Toast.error('操作失败');
        }
    }
};

window.AlertsPage = AlertsPage;
