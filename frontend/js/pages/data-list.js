/**
 * 数据列表页面
 */
const DataListPage = {
    table: null,
    pagination: null,
    filters: {
        keyword: '',
        type: '',
        page: 1,
        size: 10
    },

    init() {
        this.render();
        this.loadData();
        this.loadTypes();
    },

    render() {
        const container = document.getElementById('pageContainer');

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">数据管理</h3>
                    <button class="btn btn-primary" id="addDataBtn">新增数据</button>
                </div>
                <div class="card-body">
                    <div class="toolbar">
                        <div class="toolbar-left">
                            <div class="search-box">
                                <input type="text" class="form-control" id="searchInput" placeholder="搜索名称或描述...">
                                <button class="btn btn-primary" id="searchBtn">搜索</button>
                            </div>
                            <select class="form-control" id="typeFilter" style="width: 150px;">
                                <option value="">全部类型</option>
                            </select>
                        </div>
                        <div class="toolbar-right">
                            <button class="btn btn-danger" id="batchDeleteBtn" disabled>批量删除</button>
                            <button class="btn btn-outline" id="refreshBtn">刷新</button>
                        </div>
                    </div>
                    <div id="dataTable"></div>
                    <div id="pagination"></div>
                </div>
            </div>
        `;

        this.bindEvents();
    },

    bindEvents() {
        // 搜索
        document.getElementById('searchBtn')?.addEventListener('click', () => this.search());
        document.getElementById('searchInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });

        // 类型筛选
        document.getElementById('typeFilter')?.addEventListener('change', (e) => {
            this.filters.type = e.target.value;
            this.filters.page = 1;
            this.loadData();
        });

        // 新增
        document.getElementById('addDataBtn')?.addEventListener('click', () => this.showAddModal());

        // 刷新
        document.getElementById('refreshBtn')?.addEventListener('click', () => this.loadData());

        // 批量删除
        document.getElementById('batchDeleteBtn')?.addEventListener('click', () => this.batchDelete());
    },

    async loadData() {
        try {
            const response = await DataService.getList(this.filters);

            if (response.code === 200) {
                this.renderTable(response.data);
                this.renderPagination(response.data);
            }
        } catch (error) {
            Toast.error('加载数据失败');
        }
    },

    async loadTypes() {
        try {
            const response = await DataService.getTypes();
            if (response.code === 200 && response.data) {
                const select = document.getElementById('typeFilter');
                response.data.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('加载类型失败:', error);
        }
    },

    renderTable(data) {
        const container = document.getElementById('dataTable');

        this.table = new DataTable(container, {
            columns: [
                { field: 'name', title: '名称' },
                { field: 'type', title: '类型', render: (v) => `<span class="badge badge-primary">${Validator.sanitize(v)}</span>` },
                { field: 'description', title: '描述', render: (v) => Formatter.truncate(v, 30) },
                { field: 'createTime', title: '创建时间', render: (v) => Formatter.formatDate(v) }
            ],
            data: data.items || [],
            pageSize: this.filters.size,
            currentPage: this.filters.page,
            onSelectionChange: (ids) => {
                document.getElementById('batchDeleteBtn').disabled = ids.length === 0;
            }
        });

        // 添加操作按钮
        const rows = container.querySelectorAll('tbody tr');
        (data.items || []).forEach((item, idx) => {
            const actionsCell = rows[idx]?.querySelector('.actions-cell');
            if (actionsCell) {
                actionsCell.innerHTML = `
                    <button class="btn btn-sm btn-outline" onclick="DataListPage.edit(${item.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="DataListPage.delete(${item.id})">删除</button>
                `;
            }
        });
    },

    renderPagination(data) {
        const container = document.getElementById('pagination');

        this.pagination = new Pagination(container, {
            total: data.total || 0,
            pageSize: this.filters.size,
            currentPage: this.filters.page,
            onChange: ({ page, pageSize }) => {
                this.filters.page = page;
                this.filters.size = pageSize;
                this.loadData();
            }
        });
    },

    search() {
        const keyword = document.getElementById('searchInput')?.value.trim();
        this.filters.keyword = keyword;
        this.filters.page = 1;
        this.loadData();
    },

    showAddModal() {
        const modal = new Modal({
            title: '新增数据',
            content: this.getFormHTML(),
            width: '500px',
            confirmText: '保存',
            onConfirm: () => this.save(modal)
        }).show();
    },

    async edit(id) {
        try {
            const response = await DataService.getById(id);
            if (response.code === 200) {
                const modal = new Modal({
                    title: '编辑数据',
                    content: this.getFormHTML(response.data),
                    width: '500px',
                    confirmText: '保存',
                    onConfirm: () => this.save(modal, id)
                }).show();
            }
        } catch (error) {
            Toast.error('获取数据失败');
        }
    },

    async delete(id) {
        const confirmed = await Modal.confirm('确定要删除这条数据吗？');
        if (confirmed) {
            try {
                const response = await DataService.delete(id);
                if (response.code === 200) {
                    Toast.success('删除成功');
                    this.loadData();
                } else {
                    Toast.error(response.message);
                }
            } catch (error) {
                Toast.error('删除失败');
            }
        }
    },

    async batchDelete() {
        const ids = this.table?.getSelectedIds() || [];
        if (ids.length === 0) return;

        const confirmed = await Modal.confirm(`确定要删除选中的 ${ids.length} 条数据吗？`);
        if (confirmed) {
            try {
                const response = await DataService.batchDelete(ids.map(Number));
                if (response.code === 200) {
                    Toast.success(`成功删除 ${response.data.count} 条数据`);
                    this.loadData();
                } else {
                    Toast.error(response.message);
                }
            } catch (error) {
                Toast.error('批量删除失败');
            }
        }
    },

    getFormHTML(data = {}) {
        return `
            <form id="dataForm">
                <div class="form-group">
                    <label class="form-label">名称 <span style="color: red;">*</span></label>
                    <input type="text" class="form-control" name="name" value="${Validator.sanitize(data.name || '')}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">类型 <span style="color: red;">*</span></label>
                    <input type="text" class="form-control" name="type" value="${Validator.sanitize(data.type || '')}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">值</label>
                    <textarea class="form-control" name="value" rows="3">${Validator.sanitize(data.value || '')}</textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">描述</label>
                    <textarea class="form-control" name="description" rows="2">${Validator.sanitize(data.description || '')}</textarea>
                </div>
            </form>
        `;
    },

    async save(modal, id = null) {
        const form = document.getElementById('dataForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // 验证
        if (!data.name || !data.type) {
            Toast.error('请填写必填项');
            return false;
        }

        modal.setLoading(true);

        try {
            const response = id
                ? await DataService.update(id, data)
                : await DataService.create(data);

            if (response.code === 200 || response.code === 201) {
                Toast.success(id ? '更新成功' : '创建成功');
                this.loadData();
                return true;
            } else {
                Toast.error(response.message);
                return false;
            }
        } catch (error) {
            Toast.error('保存失败');
            return false;
        } finally {
            modal.setLoading(false);
        }
    },

    destroy() {
        this.table = null;
        this.pagination = null;
    }
};

// 全局可用
window.DataListPage = DataListPage;
