/**
 * 统计分析页面
 */
const StatisticsPage = {
    init() {
        this.loadStatistics();
    },

    async loadStatistics() {
        try {
            const [overviewRes, typeRes] = await Promise.all([
                StatisticsService.getOverview(),
                StatisticsService.getTypeStatistics()
            ]);

            if (overviewRes.code === 200 && typeRes.code === 200) {
                this.render(overviewRes.data, typeRes.data);
            }
        } catch (error) {
            Toast.error('加载统计数据失败');
        }
    },

    render(overview, types) {
        const container = document.getElementById('pageContainer');

        container.innerHTML = `
            <div class="stat-cards">
                <div class="stat-card">
                    <div class="stat-card-icon primary">📊</div>
                    <div class="stat-card-title">总数据量</div>
                    <div class="stat-card-value">${Formatter.formatNumber(overview.totalCount || 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon success">📈</div>
                    <div class="stat-card-title">今日新增</div>
                    <div class="stat-card-value">${Formatter.formatNumber(overview.todayCount || 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon warning">📁</div>
                    <div class="stat-card-title">数据类型数</div>
                    <div class="stat-card-value">${types.length}</div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">类型统计</h3>
                    </div>
                    <div class="card-body">
                        <div class="table-wrapper">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>类型</th>
                                        <th>数量</th>
                                        <th>占比</th>
                                        <th>最后更新</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${this.renderTypeTable(types, overview.totalCount)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">趋势分析</h3>
                    </div>
                    <div class="card-body">
                        ${this.renderTrendChart(overview.trend)}
                    </div>
                </div>
            </div>
        `;
    },

    renderTypeTable(types, total) {
        if (!types || types.length === 0) {
            return '<tr><td colspan="4" class="empty-text">暂无数据</td></tr>';
        }

        return types.map(item => `
            <tr>
                <td><span class="badge badge-primary">${Validator.sanitize(item.type)}</span></td>
                <td>${Formatter.formatNumber(item.count)}</td>
                <td>${Formatter.formatPercent(item.count / total)}</td>
                <td>${Formatter.formatDate(item.lastUpdate)}</td>
            </tr>
        `).join('');
    },

    renderTrendChart(trend) {
        if (!trend || !trend.labels || !trend.values) {
            return '<p class="empty-text">暂无数据</p>';
        }

        const maxValue = Math.max(...trend.values, 1);

        return `
            <div style="display: flex; align-items: flex-end; height: 250px; gap: 16px; padding-top: 20px;">
                ${trend.labels.map((label, i) => {
                    const value = trend.values[i];
                    const height = (value / maxValue * 200);
                    return `
                        <div style="flex: 1; text-align: center;">
                            <div style="
                                background: linear-gradient(to top, var(--primary-color), #6fa8ff);
                                height: ${Math.max(height, 4)}px;
                                border-radius: 4px 4px 0 0;
                                margin-bottom: 8px;
                                transition: height 0.3s;
                            " title="${value}"></div>
                            <div style="font-size: 12px; color: var(--text-secondary);">${label}</div>
                            <div style="font-weight: bold; font-size: 14px;">${value}</div>
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
window.StatisticsPage = StatisticsPage;
