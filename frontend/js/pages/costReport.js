/**
 * 成本报表页面
 */
const CostReportPage = {
    currentDimension: 'product',
    chart: null,
    pieChart: null,

    render(container) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">成本分析报表</h3>
                    <div style="display: flex; gap: 8px;">
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-sm ${this.currentDimension === 'product' ? 'btn-primary' : 'btn-outline'}" onclick="CostReportPage.switchDimension('product')">按产品</button>
                            <button type="button" class="btn btn-sm ${this.currentDimension === 'line' ? 'btn-primary' : 'btn-outline'}" onclick="CostReportPage.switchDimension('line')">按生产线</button>
                            <button type="button" class="btn btn-sm ${this.currentDimension === 'month' ? 'btn-primary' : 'btn-outline'}" onclick="CostReportPage.switchDimension('month')">按月份</button>
                            <button type="button" class="btn btn-sm ${this.currentDimension === 'element' ? 'btn-primary' : 'btn-outline'}" onclick="CostReportPage.switchDimension('element')">按要素</button>
                        </div>
                        <button class="btn btn-outline btn-sm" onclick="CostReportPage.exportCSV()">
                            📥 导出CSV
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="grid grid-2">
                        <div class="card" style="box-shadow: none; border: 1px solid var(--border-light); margin-bottom: 0;">
                            <div class="card-header" style="padding: 12px 16px;">
                                <h4 class="card-title" style="font-size: 14px; margin: 0;">成本构成柱状图</h4>
                            </div>
                            <div class="card-body" style="padding: 16px;">
                                <canvas id="costBarChart" style="height: 300px;"></canvas>
                            </div>
                        </div>
                        <div class="card" style="box-shadow: none; border: 1px solid var(--border-light); margin-bottom: 0;">
                            <div class="card-header" style="padding: 12px 16px;">
                                <h4 class="card-title" style="font-size: 14px; margin: 0;">要素占比</h4>
                            </div>
                            <div class="card-body" style="padding: 16px;">
                                <canvas id="costPieChart" style="height: 300px;"></canvas>
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 20px;">
                        <div class="card" style="box-shadow: none; border: 1px solid var(--border-light); margin-bottom: 0;">
                            <div class="card-header" style="padding: 12px 16px;">
                                <h4 class="card-title" style="font-size: 14px; margin: 0;">数据透视表</h4>
                            </div>
                            <div class="card-body" style="padding: 0;">
                                <div id="pivotTable" style="overflow-x: auto;"></div>
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 20px;">
                        <div class="card" style="box-shadow: none; border: 1px solid var(--border-light); margin-bottom: 0;">
                            <div class="card-header" style="padding: 12px 16px;">
                                <h4 class="card-title" style="font-size: 14px; margin: 0;">月度成本趋势（含同比环比）</h4>
                            </div>
                            <div class="card-body" style="padding: 0;">
                                <div id="monthlyTable" style="overflow-x: auto;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.loadReportData();
        this.loadMonthlyData();
    },

    async switchDimension(dimension) {
        this.currentDimension = dimension;
        document.querySelectorAll('.btn-group .btn').forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline');
        });
        event.target.classList.remove('btn-outline');
        event.target.classList.add('btn-primary');
        await this.loadReportData();
    },

    async loadReportData() {
        try {
            const response = await CostService.getMultiDimensionReport({
                dimension: this.currentDimension
            });

            if (response.code === 200) {
                this.renderChart(response.data);
                this.renderPieChart(response.data.type_totals);
                this.renderPivotTable(response.data.pivot_data);
            }
        } catch (error) {
            console.error('加载报表数据失败:', error);
            Toast.error('加载报表数据失败');
        }
    },

    renderChart(data) {
        if (this.chart) {
            this.chart.destroy();
        }

        const ctx = document.getElementById('costBarChart');
        if (!ctx) return;

        const colors = {
            material: 'rgba(0, 123, 255, 0.8)',
            labor: 'rgba(40, 167, 69, 0.8)',
            depreciation: 'rgba(23, 162, 184, 0.8)',
            energy: 'rgba(255, 193, 7, 0.8)',
            other: 'rgba(108, 117, 125, 0.8)'
        };

        const typeLabels = {
            material: '原材料',
            labor: '人工',
            depreciation: '设备折旧',
            energy: '能源',
            other: '其他'
        };

        const datasets = ['material', 'labor', 'depreciation', 'energy', 'other'].map(type => ({
            label: typeLabels[type],
            data: data.datasets[type],
            backgroundColor: colors[type],
            borderColor: colors[type].replace('0.8', '1'),
            borderWidth: 1
        }));

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + Formatter.formatNumber(value);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ¥' + Formatter.formatNumber(context.raw);
                            }
                        }
                    }
                }
            }
        });
    },

    renderPieChart(typeTotals) {
        if (this.pieChart) {
            this.pieChart.destroy();
        }

        const ctx = document.getElementById('costPieChart');
        if (!ctx) return;

        const colors = [
            'rgba(0, 123, 255, 0.8)',
            'rgba(40, 167, 69, 0.8)',
            'rgba(23, 162, 184, 0.8)',
            'rgba(255, 193, 7, 0.8)',
            'rgba(108, 117, 125, 0.8)'
        ];

        const typeLabels = {
            material: '原材料',
            labor: '人工',
            depreciation: '设备折旧',
            energy: '能源',
            other: '其他'
        };

        const labels = [];
        const values = [];
        const backgroundColors = [];

        Object.entries(typeTotals).forEach(([type, value], index) => {
            if (value > 0) {
                labels.push(typeLabels[type]);
                values.push(value);
                backgroundColors.push(colors[index]);
            }
        });

        if (values.every(v => v === 0)) {
            ctx.parentElement.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">暂无数据</div>';
            return;
        }

        this.pieChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColors,
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
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return context.label + ': ¥' + Formatter.formatNumber(context.raw) + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    },

    renderPivotTable(pivotData) {
        const container = document.getElementById('pivotTable');
        if (!container) return;

        const typeLabels = {
            material: '原材料',
            labor: '人工',
            depreciation: '设备折旧',
            energy: '能源',
            other: '其他',
            total: '合计'
        };

        const dimensionLabels = {
            product: '产品',
            line: '生产线',
            month: '月份',
            element: '要素'
        };

        if (!pivotData || pivotData.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">暂无数据</div>';
            return;
        }

        let html = `
            <table class="table table-hover" style="margin-bottom: 0;">
                <thead>
                    <tr style="background: var(--bg-light);">
                        <th>${dimensionLabels[this.currentDimension] || '维度'}</th>
                        <th style="text-align: right;">原材料(元)</th>
                        <th style="text-align: right;">人工(元)</th>
                        <th style="text-align: right;">设备折旧(元)</th>
                        <th style="text-align: right;">能源(元)</th>
                        <th style="text-align: right;">其他(元)</th>
                        <th style="text-align: right; font-weight: bold;">合计(元)</th>
                    </tr>
                </thead>
                <tbody>
        `;

        const totals = { material: 0, labor: 0, depreciation: 0, energy: 0, other: 0, total: 0 };

        pivotData.forEach(row => {
            totals.material += row.material;
            totals.labor += row.labor;
            totals.depreciation += row.depreciation;
            totals.energy += row.energy;
            totals.other += row.other;
            totals.total += row.total;

            html += `
                <tr>
                    <td><strong>${Validator.sanitize(row.dimension)}</strong></td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.material)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.labor)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.depreciation)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.energy)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.other)}</td>
                    <td style="text-align: right; font-weight: bold;">${Formatter.formatNumber(row.total)}</td>
                </tr>
            `;
        });

        html += `
                <tr style="background: var(--bg-light); font-weight: bold;">
                    <td>合计</td>
                    <td style="text-align: right;">${Formatter.formatNumber(totals.material)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(totals.labor)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(totals.depreciation)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(totals.energy)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(totals.other)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(totals.total)}</td>
                </tr>
                </tbody>
            </table>
        `;

        container.innerHTML = html;
    },

    async loadMonthlyData() {
        try {
            const response = await CostService.getMonthlySummary(12);
            if (response.code === 200) {
                this.renderMonthlyTable(response.data);
            }
        } catch (error) {
            console.error('加载月度数据失败:', error);
        }
    },

    renderMonthlyTable(monthlyData) {
        const container = document.getElementById('monthlyTable');
        if (!container) return;

        if (!monthlyData || monthlyData.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">暂无数据</div>';
            return;
        }

        let html = `
            <table class="table table-hover" style="margin-bottom: 0;">
                <thead>
                    <tr style="background: var(--bg-light);">
                        <th>月份</th>
                        <th style="text-align: right;">原材料(元)</th>
                        <th style="text-align: right;">人工(元)</th>
                        <th style="text-align: right;">设备折旧(元)</th>
                        <th style="text-align: right;">能源(元)</th>
                        <th style="text-align: right;">其他(元)</th>
                        <th style="text-align: right;">总成本(元)</th>
                        <th style="text-align: right;">环比</th>
                        <th style="text-align: right;">同比</th>
                    </tr>
                </thead>
                <tbody>
        `;

        monthlyData.forEach(row => {
            const momClass = row.mom > 0 ? 'text-danger' : row.mom < 0 ? 'text-success' : 'text-muted';
            const yoyClass = row.yoy > 0 ? 'text-danger' : row.yoy < 0 ? 'text-success' : 'text-muted';
            const momIcon = row.mom > 0 ? '↑' : row.mom < 0 ? '↓' : '-';
            const yoyIcon = row.yoy > 0 ? '↑' : row.yoy < 0 ? '↓' : '-';

            html += `
                <tr>
                    <td><strong>${row.month}</strong></td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.material)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.labor)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.depreciation)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.energy)}</td>
                    <td style="text-align: right;">${Formatter.formatNumber(row.other)}</td>
                    <td style="text-align: right; font-weight: bold;">${Formatter.formatNumber(row.total)}</td>
                    <td style="text-align: right;" class="${momClass}">
                        ${row.mom !== null ? `${momIcon} ${Math.abs(row.mom)}%` : '-'}
                    </td>
                    <td style="text-align: right;" class="${yoyClass}">
                        ${row.yoy !== null ? `${yoyIcon} ${Math.abs(row.yoy)}%` : '-'}
                    </td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        container.innerHTML = html;
    },

    async exportCSV() {
        try {
            const response = await CostService.exportCSV({
                dimension: this.currentDimension
            });

            if (response.code === 200) {
                const { filename, content } = response.data;
                const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                Toast.success('导出成功');
            } else {
                Toast.error(response.message || '导出失败');
            }
        } catch (error) {
            console.error('导出失败:', error);
            Toast.error('导出失败');
        }
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

window.CostReportPage = CostReportPage;
