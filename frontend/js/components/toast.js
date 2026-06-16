/**
 * 提示框组件
 */
const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.getElementById('toastContainer');
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'toastContainer';
                this.container.className = 'toast-container';
                document.body.appendChild(this.container);
            }
        }
    },

    /**
     * 显示提示
     * @param {string} message - 消息内容
     * @param {string} type - 类型: success/error/warning/info
     * @param {number} duration - 显示时长(毫秒)
     */
    show(message, type = 'info', duration = 3000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        this.container.appendChild(toast);

        // 自动移除
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, duration);
    },

    /**
     * 成功提示
     */
    success(message, duration) {
        this.show(message, 'success', duration);
    },

    /**
     * 错误提示
     */
    error(message, duration) {
        this.show(message, 'error', duration);
    },

    /**
     * 警告提示
     */
    warning(message, duration) {
        this.show(message, 'warning', duration);
    },

    /**
     * 信息提示
     */
    info(message, duration) {
        this.show(message, 'info', duration);
    }
};

// 全局可用
window.Toast = Toast;
