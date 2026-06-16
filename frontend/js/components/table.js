/**
 * 数据表格组件
 */
class DataTable {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            columns: options.columns || [],
            data: options.data || [],
            pageSize: options.pageSize || 10,
            currentPage: options.currentPage || 1,
            showCheckbox: options.showCheckbox !== false,
            showIndex: options.showIndex !== false,
            emptyText: options.emptyText || '暂无数据',
            onRowClick: options.onRowClick || null,
            onSelectionChange: options.onSelectionChange || null
        };

        this.selectedRows = [];
        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        const { columns, data, showCheckbox, showIndex, emptyText, currentPage, pageSize } = this.options;

        let html = '<div class="table-wrapper"><table class="data-table"><thead><tr>';

        // 表头
        if (showCheckbox) {
            html += '<th class="checkbox-cell"><input type="checkbox" class="select-all"></th>';
        }
        if (showIndex) {
            html += '<th>序号</th>';
        }

        columns.forEach(col => {
            const sortable = col.sortable ? `data-sortable="true" data-field="${col.field}"` : '';
            html += `<th ${sortable}>${col.title}${col.sortable ? '<span class="sort-icon">↕</span>' : ''}</th>`;
        });

        html += '<th class="actions-cell">操作</th>';
        html += '</tr></thead><tbody>';

        // 表体
        if (data.length === 0) {
            const colSpan = columns.length + (showCheckbox ? 1 : 0) + (showIndex ? 1 : 0) + 1;
            html += `<tr><td colspan="${colSpan}" class="empty-text">${emptyText}</td></tr>`;
        } else {
            const startIdx = (currentPage - 1) * pageSize;
            data.forEach((row, idx) => {
                html += '<tr>';
                if (showCheckbox) {
                    html += `<td class="checkbox-cell"><input type="checkbox" class="row-checkbox" data-id="${row.id}"></td>`;
                }
                if (showIndex) {
                    html += `<td>${startIdx + idx + 1}</td>`;
                }
                columns.forEach(col => {
                    const value = row[col.field];
                    const displayValue = col.render ? col.render(value, row) : (value ?? '-');
                    html += `<td>${displayValue}</td>`;
                });
                html += '<td class="actions-cell"></td>';
                html += '</tr>';
            });
        }

        html += '</tbody></table></div>';
        this.container.innerHTML = html;
    }

    bindEvents() {
        // 全选事件
        const selectAll = this.container.querySelector('.select-all');
        selectAll?.addEventListener('change', (e) => {
            const checkboxes = this.container.querySelectorAll('.row-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
            this.updateSelection();
        });

        // 单行选择
        this.container.querySelectorAll('.row-checkbox').forEach(cb => {
            cb.addEventListener('change', () => this.updateSelection());
        });

        // 行点击
        if (this.options.onRowClick) {
            this.container.querySelectorAll('tbody tr').forEach(tr => {
                tr.addEventListener('click', (e) => {
                    if (e.target.type !== 'checkbox') {
                        this.options.onRowClick(tr);
                    }
                });
            });
        }

        // 排序
        this.container.querySelectorAll('[data-sortable="true"]').forEach(th => {
            th.addEventListener('click', () => {
                const field = th.dataset.field;
                this.sort(field);
            });
        });
    }

    updateSelection() {
        this.selectedRows = Array.from(
            this.container.querySelectorAll('.row-checkbox:checked')
        ).map(cb => cb.dataset.id);

        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(this.selectedRows);
        }
    }

    setData(data) {
        this.options.data = data;
        this.render();
        this.bindEvents();
    }

    sort(field) {
        const currentOrder = this.sortOrder || 'asc';
        this.sortOrder = currentOrder === 'asc' ? 'desc' : 'asc';

        this.options.data.sort((a, b) => {
            const aVal = a[field];
            const bVal = b[field];

            if (aVal === bVal) return 0;
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;

            const result = aVal > bVal ? 1 : -1;
            return this.sortOrder === 'asc' ? result : -result;
        });

        this.render();
        this.bindEvents();
    }

    getSelectedIds() {
        return this.selectedRows;
    }

    clearSelection() {
        this.container.querySelectorAll('.row-checkbox').forEach(cb => {
            cb.checked = false;
        });
        const selectAll = this.container.querySelector('.select-all');
        if (selectAll) selectAll.checked = false;
        this.selectedRows = [];
    }
}

// 全局可用
window.DataTable = DataTable;
