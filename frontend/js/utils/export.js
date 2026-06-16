/**
 * 数据导出工具
 */
const ExportUtils = {
    /**
     * 将数据导出为CSV文件
     * @param {Array} data - 数据数组
     * @param {Array} columns - 列定义 [{title: '列名', field: 'fieldName'}, ...]
     * @param {string} filename - 文件名（不含扩展名）
     */
    exportToCSV(data, columns, filename = 'data') {
        if (!data || data.length === 0) {
            Toast.warning('没有数据可导出');
            return;
        }

        try {
            // 构建CSV内容
            const headers = columns.map(col => `"${col.title}"`).join(',');
            const rows = data.map(item => {
                return columns.map(col => {
                    let value = item[col.field];
                    
                    // 处理特殊值
                    if (value === null || value === undefined) {
                        value = '';
                    } else if (typeof value === 'object') {
                        value = JSON.stringify(value);
                    } else if (typeof value === 'boolean') {
                        value = value ? '是' : '否';
                    }
                    
                    // 转义引号和逗号
                    value = String(value).replace(/"/g, '""');
                    return `"${value}"`;
                }).join(',');
            });

            const csvContent = [headers, ...rows].join('\n');
            
            // 创建下载链接
            const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            
            link.href = url;
            link.setAttribute('download', `${filename}_${new Date().getTime()}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            Toast.success('数据导出成功');
            
        } catch (error) {
            console.error('导出CSV失败:', error);
            Toast.error('导出失败');
        }
    },

    /**
     * 将数据导出为Excel文件（使用CSV格式模拟）
     * @param {Array} data - 数据数组
     * @param {Array} columns - 列定义
     * @param {string} filename - 文件名（不含扩展名）
     */
    exportToExcel(data, columns, filename = 'data') {
        this.exportToCSV(data, columns, filename);
    },

    /**
     * 将数据导出为JSON文件
     * @param {Array} data - 数据数组
     * @param {string} filename - 文件名（不含扩展名）
     */
    exportToJSON(data, filename = 'data') {
        if (!data || data.length === 0) {
            Toast.warning('没有数据可导出');
            return;
        }

        try {
            const jsonContent = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            
            link.href = url;
            link.setAttribute('download', `${filename}_${new Date().getTime()}.json`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            Toast.success('JSON导出成功');
            
        } catch (error) {
            console.error('导出JSON失败:', error);
            Toast.error('导出失败');
        }
    },

    /**
     * 导出图表为图片
     * @param {string} canvasId - Canvas元素ID
     * @param {string} filename - 文件名（不含扩展名）
     */
    exportChartToImage(canvasId, filename = 'chart') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            Toast.warning('图表未找到');
            return;
        }

        try {
            const url = canvas.toDataURL('image/png');
            const link = document.createElement('a');
            
            link.href = url;
            link.setAttribute('download', `${filename}_${new Date().getTime()}.png`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            Toast.success('图表导出成功');
            
        } catch (error) {
            console.error('导出图表失败:', error);
            Toast.error('导出失败');
        }
    }
};

// 全局可用
window.ExportUtils = ExportUtils;