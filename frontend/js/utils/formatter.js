/**
 * 数据格式化工具模块
 */
const Formatter = {
    /**
     * 格式化日期时间
     * @param {string|Date} date - 日期
     * @param {string} format - 格式
     * @returns {string}
     */
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        if (!date) return '';

        const d = new Date(date);
        if (isNaN(d.getTime())) return '';

        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },

    /**
     * 格式化日期
     * @param {string|Date} date - 日期
     * @returns {string}
     */
    formatDateOnly(date) {
        return this.formatDate(date, 'YYYY-MM-DD');
    },

    /**
     * 格式化时间
     * @param {string|Date} date - 日期
     * @returns {string}
     */
    formatTimeOnly(date) {
        return this.formatDate(date, 'HH:mm:ss');
    },

    /**
     * 格式化数字
     * @param {number} num - 数字
     * @param {number} decimals - 小数位数
     * @returns {string}
     */
    formatNumber(num, decimals = 0) {
        if (isNaN(num)) return '0';
        return Number(num).toLocaleString('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },

    /**
     * 格式化货币
     * @param {number} amount - 金额
     * @returns {string}
     */
    formatCurrency(amount) {
        if (isNaN(amount)) return '¥0.00';
        return '¥' + this.formatNumber(amount, 2);
    },

    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     * @returns {string}
     */
    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';

        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        const k = 1024;
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + units[i];
    },

    /**
     * 格式化百分比
     * @param {number} value - 值
     * @param {number} decimals - 小数位数
     * @returns {string}
     */
    formatPercent(value, decimals = 1) {
        if (isNaN(value)) return '0%';
        return (value * 100).toFixed(decimals) + '%';
    },

    /**
     * 截断文本
     * @param {string} text - 文本
     * @param {number} length - 最大长度
     * @param {string} suffix - 后缀
     * @returns {string}
     */
    truncate(text, length = 50, suffix = '...') {
        if (!text) return '';
        if (text.length <= length) return text;
        return text.substring(0, length) + suffix;
    },

    /**
     * 首字母大写
     * @param {string} str - 字符串
     * @returns {string}
     */
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * 驼峰转下划线
     * @param {string} str - 字符串
     * @returns {string}
     */
    camelToSnake(str) {
        return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    },

    /**
     * 下划线转驼峰
     * @param {string} str - 字符串
     * @returns {string}
     */
    snakeToCamel(str) {
        return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    }
};

// 全局可用
window.Formatter = Formatter;
