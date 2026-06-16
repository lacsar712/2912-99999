/**
 * 分页组件
 */
class Pagination {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            total: options.total || 0,
            pageSize: options.pageSize || 10,
            currentPage: options.currentPage || 1,
            pageSizes: options.pageSizes || [10, 20, 50, 100],
            onChange: options.onChange || null
        };

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        const { total, pageSize, currentPage, pageSizes } = this.options;
        const totalPages = Math.ceil(total / pageSize) || 1;

        let html = '<div class="pagination">';

        // 分页信息
        html += `<span class="pagination-info">共 ${total} 条</span>`;

        // 每页条数选择
        html += '<select class="form-control page-size-select" style="width: auto;">';
        pageSizes.forEach(size => {
            html += `<option value="${size}" ${size === pageSize ? 'selected' : ''}>${size} 条/页</option>`;
        });
        html += '</select>';

        // 上一页
        html += `<button class="pagination-btn prev-btn" ${currentPage <= 1 ? 'disabled' : ''}>‹</button>`;

        // 页码
        const pages = this.getPageNumbers(currentPage, totalPages);
        pages.forEach(page => {
            if (page === '...') {
                html += '<span class="pagination-btn">...</span>';
            } else {
                html += `<button class="pagination-btn page-btn ${page === currentPage ? 'active' : ''}" data-page="${page}">${page}</button>`;
            }
        });

        // 下一页
        html += `<button class="pagination-btn next-btn" ${currentPage >= totalPages ? 'disabled' : ''}>›</button>`;

        html += '</div>';
        this.container.innerHTML = html;
    }

    getPageNumbers(current, total) {
        const pages = [];

        if (total <= 7) {
            for (let i = 1; i <= total; i++) {
                pages.push(i);
            }
        } else {
            if (current <= 4) {
                pages.push(1, 2, 3, 4, 5, '...', total);
            } else if (current >= total - 3) {
                pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total);
            } else {
                pages.push(1, '...', current - 1, current, current + 1, '...', total);
            }
        }

        return pages;
    }

    bindEvents() {
        // 页码点击
        this.container.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = parseInt(btn.dataset.page);
                this.goToPage(page);
            });
        });

        // 上一页
        this.container.querySelector('.prev-btn')?.addEventListener('click', () => {
            if (this.options.currentPage > 1) {
                this.goToPage(this.options.currentPage - 1);
            }
        });

        // 下一页
        this.container.querySelector('.next-btn')?.addEventListener('click', () => {
            const totalPages = Math.ceil(this.options.total / this.options.pageSize);
            if (this.options.currentPage < totalPages) {
                this.goToPage(this.options.currentPage + 1);
            }
        });

        // 每页条数
        this.container.querySelector('.page-size-select')?.addEventListener('change', (e) => {
            this.options.pageSize = parseInt(e.target.value);
            this.options.currentPage = 1;
            this.triggerChange();
        });
    }

    goToPage(page) {
        this.options.currentPage = page;
        this.triggerChange();
    }

    triggerChange() {
        if (this.options.onChange) {
            this.options.onChange({
                page: this.options.currentPage,
                pageSize: this.options.pageSize
            });
        }
        this.render();
        this.bindEvents();
    }

    setTotal(total) {
        this.options.total = total;
        this.render();
        this.bindEvents();
    }

    setPage(page) {
        this.options.currentPage = page;
        this.render();
        this.bindEvents();
    }
}

// 全局可用
window.Pagination = Pagination;
