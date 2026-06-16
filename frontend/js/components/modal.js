/**
 * 模态框组件
 */
class Modal {
    constructor(options = {}) {
        this.options = {
            title: options.title || '提示',
            content: options.content || '',
            width: options.width || '500px',
            showFooter: options.showFooter !== false,
            confirmText: options.confirmText || '确定',
            cancelText: options.cancelText || '取消',
            onConfirm: options.onConfirm || null,
            onCancel: options.onCancel || null,
            closeOnOverlay: options.closeOnOverlay !== false
        };

        this.overlay = null;
        this.modal = null;
        this.init();
    }

    init() {
        // 创建遮罩层
        this.overlay = document.createElement('div');
        this.overlay.className = 'modal-overlay';

        // 创建模态框
        this.modal = document.createElement('div');
        this.modal.className = 'modal';
        this.modal.style.maxWidth = this.options.width;

        // 构建HTML
        let html = `
            <div class="modal-header">
                <h3 class="modal-title">${Validator.sanitize(this.options.title)}</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">${this.options.content}</div>
        `;

        if (this.options.showFooter) {
            html += `
                <div class="modal-footer">
                    <button class="btn btn-outline modal-cancel">${this.options.cancelText}</button>
                    <button class="btn btn-primary modal-confirm">${this.options.confirmText}</button>
                </div>
            `;
        }

        this.modal.innerHTML = html;
        this.overlay.appendChild(this.modal);
        document.body.appendChild(this.overlay);

        // 绑定事件
        this.bindEvents();
    }

    bindEvents() {
        // 关闭按钮
        const closeBtn = this.modal.querySelector('.modal-close');
        closeBtn?.addEventListener('click', () => this.close());

        // 取消按钮
        const cancelBtn = this.modal.querySelector('.modal-cancel');
        cancelBtn?.addEventListener('click', () => {
            if (this.options.onCancel) {
                this.options.onCancel();
            }
            this.close();
        });

        // 确认按钮
        const confirmBtn = this.modal.querySelector('.modal-confirm');
        confirmBtn?.addEventListener('click', () => {
            if (this.options.onConfirm) {
                const result = this.options.onConfirm();
                if (result !== false) {
                    this.close();
                }
            } else {
                this.close();
            }
        });

        // 遮罩层点击关闭
        if (this.options.closeOnOverlay) {
            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) {
                    this.close();
                }
            });
        }

        // ESC键关闭
        document.addEventListener('keydown', this.handleEsc = (e) => {
            if (e.key === 'Escape') {
                this.close();
            }
        });
    }

    show() {
        this.overlay.classList.add('show');
        return this;
    }

    close() {
        this.overlay.classList.remove('show');
        document.removeEventListener('keydown', this.handleEsc);
        setTimeout(() => {
            this.overlay.remove();
        }, 300);
        return this;
    }

    setContent(content) {
        const body = this.modal.querySelector('.modal-body');
        if (body) {
            body.innerHTML = content;
        }
        return this;
    }

    setLoading(loading) {
        const confirmBtn = this.modal.querySelector('.modal-confirm');
        if (confirmBtn) {
            confirmBtn.disabled = loading;
            confirmBtn.textContent = loading ? '处理中...' : this.options.confirmText;
        }
        return this;
    }

    /**
     * 确认对话框
     */
    static confirm(message, options = {}) {
        return new Promise((resolve) => {
            new Modal({
                title: options.title || '确认',
                content: `<p>${Validator.sanitize(message)}</p>`,
                width: '400px',
                onConfirm: () => resolve(true),
                onCancel: () => resolve(false)
            }).show();
        });
    }

    /**
     * 提示对话框
     */
    static alert(message, options = {}) {
        return new Promise((resolve) => {
            new Modal({
                title: options.title || '提示',
                content: `<p>${Validator.sanitize(message)}</p>`,
                width: '400px',
                showFooter: false,
                onConfirm: () => resolve(true)
            }).show();
        });
    }
}

// 全局可用
window.Modal = Modal;
