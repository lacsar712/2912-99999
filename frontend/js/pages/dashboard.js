/**
 * 仪表盘页面
 */
const DashboardPage = {
    init() {
        this.loadStatistics();
    },

    async loadStatistics() {
        try {
            const response = await StatisticsService.getOverview();

            if (response.code === 200) {
                this.renderStatistics(response.data);
            }
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },

    renderStatistics(data) {
        const container = document.getElementById('pageContainer');

        container.innerHTML = `
            <div class="stat-cards">
                <div class="stat-card">
                    <div class="stat-card-icon primary">📊</div>
                    <div class="stat-card-title">总数据量</div>
                    <div class="stat-card-value">${Formatter.formatNumber(data.totalCount || 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon success">📈</div>
                    <div class="stat-card-title">今日新增</div>
                    <div class="stat-card-value">${Formatter.formatNumber(data.todayCount || 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon warning">📁</div>
                    <div class="stat-card-title">数据类型</div>
                    <div class="stat-card-value">${Object.keys(data.typeDistribution || {}).length}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon info">📅</div>
                    <div class="stat-card-title">本月数据</div>
                    <div class="stat-card-value">${Formatter.formatNumber(data.trend?.values?.slice(-1)[0] || 0)}</div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">类型分布</h3>
                    </div>
                    <div class="card-body">
                        ${this.renderTypeDistribution(data.typeDistribution || {})}
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">数据趋势</h3>
                    </div>
                    <div class="card-body">
                        ${this.renderTrend(data.trend || {})}
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">快速操作</h3>
                </div>
                <div class="card-body">
                    <div class="quick-actions">
                        <button class="btn btn-primary" onclick="App.navigate('data')">管理数据</button>
                        <button class="btn btn-secondary" onclick="App.navigate('statistics')">查看统计</button>
                        <button class="btn btn-outline" onclick="App.navigate('settings')">系统设置</button>
                    </div>
                </div>
            </div>
        `;
    },

    renderTypeDistribution(distribution) {
        const types = Object.entries(distribution);
        if (types.length === 0) {
            return '<p class="empty-text">暂无数据</p>';
        }

        const total = types.reduce((sum, [, count]) => sum + count, 0);

        return types.map(([type, count]) => `
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-light);">
                <span>${Validator.sanitize(type)}</span>
                <span>
                    <strong>${Formatter.formatNumber(count)}</strong>
                    <span style="color: var(--text-secondary); margin-left: 8px;">
                        (${Formatter.formatPercent(count / total)})
                    </span>
                </span>
            </div>
        `).join('');
    },

    renderTrend(trend) {
        if (!trend.labels || !trend.values) {
            return '<p class="empty-text">暂无数据</p>';
        }

        const maxValue = Math.max(...trend.values);

        return `
            <div style="display: flex; align-items: flex-end; height: 200px; gap: 8px;">
                ${trend.labels.map((label, i) => {
                    const value = trend.values[i];
                    const height = maxValue > 0 ? (value / maxValue * 150) : 0;
                    return `
                        <div style="flex: 1; text-align: center;">
                            <div style="
                                background: var(--primary-color);
                                height: ${height}px;
                                min-height: 4px;
                                border-radius: 4px 4px 0 0;
                                margin-bottom: 8px;
                            "></div>
                            <div style="font-size: 12px; color: var(--text-secondary);">${label}</div>
                            <div style="font-weight: bold;">${value}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    destroy() {
        // 清理资源
    }
};

// 全局可用
window.DashboardPage = DashboardPage;
