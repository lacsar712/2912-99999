/**
 * 监控中心页面
 */
const MonitorPage = {
    refreshInterval: null,
    currentPage: 1,

    init() {
        this.loadDashboard();
        // 每30秒自动刷新
        this.refreshInterval = setInterval(() => this.loadDashboard(), 30000);
    },

    async loadDashboard() {
        try {
            const response = await ProductionService.getDashboard();
            if (response.code === 200) {
                this.renderDashboard(response.data);
            }
        } catch (error) {
            console.error('加载监控数据失败:', error);
        }
    },

    renderDashboard(data) {
        const container = document.getElementById('pageContainer');

        container.innerHTML = `
            <div class="stat-cards">
                <div class="stat-card">
                    <div class="stat-card-icon primary">🏭</div>
                    <div class="stat-card-title">生产线</div>
                    <div class="stat-card-value">${data.production.running_lines}/${data.production.total_lines}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                        运行中/总计
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon success">⚙️</div>
                    <div class="stat-card-title">设备</div>
                    <div class="stat-card-value">${data.production.running_equipments}/${data.production.total_equipments}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                        运行中/总计
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon warning">📡</div>
                    <div class="stat-card-title">传感器</div>
                    <div class="stat-card-value">${data.sensors.normal}/${data.sensors.total}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                        正常/总计 ${data.sensors.warning > 0 ? `<span style="color: var(--warning-color);">(${data.sensors.warning}告警)</span>` : ''}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon info">📋</div>
                    <div class="stat-card-title">任务</div>
                    <div class="stat-card-value">${data.tasks.in_progress}/${data.tasks.total}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 8px;">
                        进行中/总计
                    </div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">今日生产概况</h3>
                    </div>
                    <div class="card-body">
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
                            <div style="text-align: center; padding: 16px; background: var(--bg-light); border-radius: 8px;">
                                <div style="font-size: 28px; font-weight: bold; color: var(--primary-color);">${data.today.products}</div>
                                <div style="font-size: 12px; color: var(--text-secondary);">生产数量</div>
                            </div>
                            <div style="text-align: center; padding: 16px; background: var(--bg-light); border-radius: 8px;">
                                <div style="font-size: 28px; font-weight: bold; color: var(--success-color);">${data.today.qualified}</div>
                                <div style="font-size: 12px; color: var(--text-secondary);">合格数量</div>
                            </div>
                            <div style="text-align: center; padding: 16px; background: var(--bg-light); border-radius: 8px;">
                                <div style="font-size: 28px; font-weight: bold; color: var(--info-color);">${data.today.yield_rate}%</div>
                                <div style="font-size: 12px; color: var(--text-secondary);">良品率</div>
                            </div>
                            <div style="text-align: center; padding: 16px; background: var(--bg-light); border-radius: 8px;">
                                <div style="font-size: 28px; font-weight: bold; ${data.alerts.active > 0 ? 'color: var(--danger-color);' : 'color: var(--success-color);'}">${data.alerts.active}</div>
                                <div style="font-size: 12px; color: var(--text-secondary);">活跃告警</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">设备状态分布</h3>
                    </div>
                    <div class="card-body">
                        ${this.renderEquipmentStatus(data.production)}
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">生产线实时状态</h3>
                    <button class="btn btn-sm btn-outline" onclick="MonitorPage.loadDashboard()">刷新</button>
                </div>
                <div class="card-body">
                    <div id="productionLines"></div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">传感器实时数据</h3>
                    </div>
                    <div class="card-body">
                        <div id="sensorData" style="max-height: 300px; overflow-y: auto;">
                            <div class="loading">加载中...</div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">活跃告警</h3>
                    </div>
                    <div class="card-body">
                        <div id="activeAlerts">
                            <p class="empty-text">暂无活跃告警</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.loadProductionLines();
        this.loadSensorData();
    },

    renderEquipmentStatus(production) {
        const total = production.total_equipments || 1;
        const running = (production.running_equipments / total * 100).toFixed(1);
        const error = (production.error_equipments / total * 100).toFixed(1);

        return `
            <div style="display: flex; height: 30px; border-radius: 4px; overflow: hidden; margin-bottom: 16px;">
                <div style="width: ${running}%; background: var(--success-color);" title="运行中: ${running}%"></div>
                <div style="width: ${error}%; background: var(--danger-color);" title="故障: ${error}%"></div>
                <div style="flex: 1; background: var(--border-color);"></div>
            </div>
            <div style="display: flex; justify-content: space-around;">
                <div style="text-align: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background: var(--success-color); border-radius: 2px; margin-right: 4px;"></span>
                    <span style="font-weight: bold;">${production.running_equipments}</span>
                    <div style="font-size: 12px; color: var(--text-secondary);">运行中</div>
                </div>
                <div style="text-align: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background: var(--danger-color); border-radius: 2px; margin-right: 4px;"></span>
                    <span style="font-weight: bold;">${production.error_equipments}</span>
                    <div style="font-size: 12px; color: var(--text-secondary);">故障</div>
                </div>
                <div style="text-align: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background: var(--border-color); border-radius: 2px; margin-right: 4px;"></span>
                    <span style="font-weight: bold;">${total - production.running_equipments - production.error_equipments}</span>
                    <div style="font-size: 12px; color: var(--text-secondary);">其他</div>
                </div>
            </div>
        `;
    },

    async loadProductionLines() {
        try {
            const response = await ProductionService.getLines({ size: 10 });
            if (response.code === 200) {
                this.renderProductionLines(response.data.items || []);
            }
        } catch (error) {
            console.error('加载生产线失败:', error);
        }
    },

    renderProductionLines(lines) {
        const container = document.getElementById('productionLines');
        if (!lines || lines.length === 0) {
            container.innerHTML = '<p class="empty-text">暂无生产线数据</p>';
            return;
        }

        container.innerHTML = lines.map(line => `
            <div style="display: flex; align-items: center; padding: 12px; border-bottom: 1px solid var(--border-light);">
                <div style="flex: 1;">
                    <div style="font-weight: 600;">${Validator.sanitize(line.line_name)}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">${Validator.sanitize(line.location || '')} | 产能: ${line.capacity || 0}</div>
                </div>
                <div style="text-align: center; margin-right: 24px;">
                    <div style="font-weight: bold;">${line.equipment_count || 0}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">设备</div>
                </div>
                <div style="text-align: center; margin-right: 24px;">
                    <div style="font-weight: bold;">${line.running_count || 0}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">运行</div>
                </div>
                <div>
                    <span class="status-badge ${line.status}">${this.getStatusText(line.status)}</span>
                </div>
            </div>
        `).join('');
    },

    getStatusText(status) {
        const statusMap = {
            'running': '运行中',
            'stopped': '已停止',
            'maintenance': '维护中',
            'error': '故障'
        };
        return statusMap[status] || status;
    },

    async loadSensorData() {
        try {
            const response = await ProductionService.getSensorRealtime();
            if (response.code === 200) {
                this.renderSensorData(response.data);
            }
        } catch (error) {
            console.error('加载传感器数据失败:', error);
        }
    },

    renderSensorData(data) {
        const container = document.getElementById('sensorData');
        if (!data || Object.keys(data).length === 0) {
            container.innerHTML = '<p class="empty-text">暂无传感器数据</p>';
            return;
        }

        let html = '';
        for (const [type, sensors] of Object.entries(data)) {
            html += `<div style="margin-bottom: 16px;"><strong>${this.getSensorTypeText(type)}</strong></div>`;
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px;">';
            sensors.forEach(sensor => {
                html += `
                    <div style="padding: 8px; background: var(--bg-light); border-radius: 4px; text-align: center;">
                        <div style="font-size: 12px; color: var(--text-secondary);">${Validator.sanitize(sensor.name)}</div>
                        <div style="font-size: 18px; font-weight: bold; font-family: 'Courier New', monospace;">
                            ${sensor.value.toFixed(1)}${sensor.unit || ''}
                        </div>
                        <span class="status-badge ${sensor.status}" style="font-size: 10px;">${this.getSensorStatusText(sensor.status)}</span>
                    </div>
                `;
            });
            html += '</div>';
        }

        container.innerHTML = html;
    },

    getSensorTypeText(type) {
        const typeMap = {
            'temperature': '温度传感器',
            'pressure': '压力传感器',
            'speed': '速度传感器',
            'humidity': '湿度传感器',
            'vibration': '振动传感器'
        };
        return typeMap[type] || type;
    },

    getSensorStatusText(status) {
        const statusMap = {
            'normal': '正常',
            'warning': '告警',
            'error': '错误',
            'offline': '离线'
        };
        return statusMap[status] || status;
    },

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
};

// 全局可用
window.MonitorPage = MonitorPage;
