/**
 * 知识库页面
 */
const KnowledgePage = {
    view: 'list', // list | detail | edit
    categoryTree: [],
    selectedCategoryId: null,
    documents: [],
    currentDoc: null,
    versionHistory: [],
    comments: [],
    searchKeyword: '',
    page: 1,
    pageSize: 10,
    total: 0,
    editingDoc: null,
    isCreating: false,
    previewContent: '',
    _activeModal: null,

    init() {
        this.view = 'list';
        this.page = 1;
        this.searchKeyword = '';
        this.selectedCategoryId = null;
        this.render();
        this.loadCategoryTree();
        this.loadDocuments();
    },

    destroy() {
        this.closeModal();
    },

    openModal(options) {
        this._activeModal = new Modal(options);
        this._activeModal.show();
        return this._activeModal;
    },

    closeModal() {
        if (this._activeModal) {
            this._activeModal.close();
            this._activeModal = null;
        }
    },

    // ==================== 渲染 ====================

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="knowledge-container">
                <div class="knowledge-sidebar">
                    <div class="knowledge-sidebar-header">
                        <h3>分类目录</h3>
                        <button class="btn btn-sm btn-primary" id="addCategoryBtn">
                            <span>+</span> 新建分类
                        </button>
                    </div>
                    <div class="knowledge-category-tree" id="categoryTree"></div>
                </div>
                <div class="knowledge-main">
                    <div class="knowledge-toolbar">
                        <div class="toolbar-left">
                            ${this.view === 'detail' || this.view === 'edit' ? `
                                <button class="btn btn-sm btn-outline" id="backToListBtn">
                                    ← 返回列表
                                </button>
                            ` : ''}
                            <div class="knowledge-search-box">
                                <input type="text" class="search-input" id="globalSearchInput" 
                                    placeholder="搜索文档标题/内容/标签..." value="${this.searchKeyword}">
                                <button class="btn btn-primary" id="searchBtn">搜索</button>
                            </div>
                        </div>
                        <div class="toolbar-right">
                            ${this.view === 'list' ? `
                                <button class="btn btn-primary" id="newDocBtn">
                                    + 新建文档
                                </button>
                            ` : ''}
                            ${this.view === 'detail' ? `
                                <button class="btn btn-primary" id="editDocBtn">
                                    编辑
                                </button>
                            ` : ''}
                            ${this.view === 'edit' ? `
                                <button class="btn btn-outline" id="cancelEditBtn">
                                    取消
                                </button>
                                <button class="btn btn-primary" id="saveDocBtn">
                                    保存
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    <div class="knowledge-content" id="knowledgeContent"></div>
                </div>
            </div>
        `;
        this.bindEvents();
        this.renderCategoryTree();
        this.renderContent();
    },

    bindEvents() {
        document.getElementById('addCategoryBtn')?.addEventListener('click', () => this.showCategoryModal());
        document.getElementById('globalSearchInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.doSearch();
            }
        });
        document.getElementById('searchBtn')?.addEventListener('click', () => this.doSearch());
        document.getElementById('newDocBtn')?.addEventListener('click', () => this.createNewDoc());
        document.getElementById('backToListBtn')?.addEventListener('click', () => this.backToList());
        document.getElementById('editDocBtn')?.addEventListener('click', () => this.editCurrentDoc());
        document.getElementById('cancelEditBtn')?.addEventListener('click', () => this.cancelEdit());
        document.getElementById('saveDocBtn')?.addEventListener('click', () => this.saveDocument());
    },

    doSearch() {
        const input = document.getElementById('globalSearchInput');
        this.searchKeyword = input?.value || '';
        this.page = 1;
        this.view = 'list';
        this.loadDocuments();
    },

    backToList() {
        this.view = 'list';
        this.currentDoc = null;
        this.render();
        this.loadDocuments();
    },

    // ==================== 分类树 ====================

    async loadCategoryTree() {
        try {
            const res = await KnowledgeService.getCategoryTree();
            if (res.code === 200) {
                this.categoryTree = res.data || [];
                this.renderCategoryTree();
            }
        } catch (e) {
            console.error('加载分类树失败:', e);
        }
    },

    renderCategoryTree() {
        const treeEl = document.getElementById('categoryTree');
        if (!treeEl) return;

        const allHtml = `
            <div class="tree-item ${this.selectedCategoryId === null ? 'active' : ''}" data-id="">
                <span class="tree-item-name">📚 全部文档</span>
            </div>
        `;

        const renderTreeItems = (items, level = 0) => {
            return items.map(item => `
                <div class="tree-item ${this.selectedCategoryId === item.id ? 'active' : ''}" 
                     data-id="${item.id}" style="padding-left: ${level * 16 + 8}px">
                    <span class="tree-toggle">${item.children && item.children.length > 0 ? '▼' : ' '}</span>
                    <span class="tree-item-name">📁 ${item.name}</span>
                    <div class="tree-item-actions">
                        <button class="tree-action-btn" data-action="add" title="添加子分类">+</button>
                        <button class="tree-action-btn" data-action="edit" title="编辑">✏️</button>
                        <button class="tree-action-btn" data-action="delete" title="删除">🗑️</button>
                    </div>
                </div>
                ${item.children && item.children.length > 0 ? renderTreeItems(item.children, level + 1) : ''}
            `).join('');
        };

        treeEl.innerHTML = allHtml + renderTreeItems(this.categoryTree);

        treeEl.querySelectorAll('.tree-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.tree-item-actions')) return;
                const id = item.dataset.id;
                this.selectedCategoryId = id ? parseInt(id) : null;
                this.page = 1;
                this.renderCategoryTree();
                this.loadDocuments();
            });
        });

        treeEl.querySelectorAll('.tree-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const itemEl = btn.closest('.tree-item');
                const id = itemEl?.dataset.id;
                
                if (action === 'add') {
                    this.showCategoryModal({ parent_id: parseInt(id) });
                } else if (action === 'edit') {
                    const category = this.findCategory(parseInt(id));
                    if (category) {
                        this.showCategoryModal(category);
                    }
                } else if (action === 'delete') {
                    this.deleteCategory(parseInt(id));
                }
            });
        });
    },

    findCategory(id, items = this.categoryTree) {
        for (const item of items) {
            if (item.id === id) return item;
            if (item.children?.length) {
                const found = this.findCategory(id, item.children);
                if (found) return found;
            }
        }
        return null;
    },

    showCategoryModal(category = null) {
        const isEdit = !!category;
        const title = isEdit ? '编辑分类' : '新建分类';
        const parentId = category?.parent_id || 0;

        this.openModal({
            title: title,
            content: `
                <form id="categoryForm">
                    <div class="form-group">
                        <label>分类名称</label>
                        <input type="text" name="name" class="form-input" value="${category?.name || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>排序号</label>
                        <input type="number" name="sort_order" class="form-input" value="${category?.sort_order || 0}">
                    </div>
                    <div class="form-group">
                        <label>描述</label>
                        <textarea name="description" class="form-input" rows="3">${category?.description || ''}</textarea>
                    </div>
                </form>
            `,
            confirmText: '保存',
            onConfirm: async () => {
                const form = document.getElementById('categoryForm');
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                data.sort_order = parseInt(data.sort_order) || 0;
                if (!isEdit && parentId) {
                    data.parent_id = parentId;
                }

                try {
                    let res;
                    if (isEdit) {
                        res = await KnowledgeService.updateCategory(category.id, data);
                    } else {
                        res = await KnowledgeService.createCategory(data);
                    }
                    if (res.code === 200 || res.code === 201) {
                        Toast.success(isEdit ? '更新成功' : '创建成功');
                        this.loadCategoryTree();
                        this.closeModal();
                    } else {
                        Toast.error(res.message || '操作失败');
                    }
                } catch (e) {
                    Toast.error('操作失败');
                }
                return false;
            }
        });
    },

    async deleteCategory(id) {
        const confirmed = await Modal.confirm('确定要删除该分类吗？');
        if (!confirmed) return;

        try {
            const res = await KnowledgeService.deleteCategory(id);
            if (res.code === 200) {
                Toast.success('删除成功');
                if (this.selectedCategoryId === id) {
                    this.selectedCategoryId = null;
                }
                this.loadCategoryTree();
                this.loadDocuments();
            } else {
                Toast.error(res.message || '删除失败');
            }
        } catch (e) {
            Toast.error('删除失败');
        }
    },

    // ==================== 文档列表 ====================

    async loadDocuments() {
        try {
            const params = {
                page: this.page,
                size: this.pageSize,
                status: 'published'
            };
            if (this.selectedCategoryId) {
                params.category_id = this.selectedCategoryId;
            }
            if (this.searchKeyword) {
                params.keyword = this.searchKeyword;
            }

            const res = await KnowledgeService.getDocuments(params);
            if (res.code === 200) {
                this.documents = res.data.items || [];
                this.total = res.data.total || 0;
                this.renderContent();
            }
        } catch (e) {
            console.error('加载文档失败:', e);
        }
    },

    renderContent() {
        const contentEl = document.getElementById('knowledgeContent');
        if (!contentEl) return;

        if (this.view === 'list') {
            this.renderDocList(contentEl);
        } else if (this.view === 'detail') {
            this.renderDocDetail(contentEl);
        } else if (this.view === 'edit') {
            this.renderDocEdit(contentEl);
        }
    },

    renderDocList(container) {
        if (this.documents.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📄</div>
                    <div class="empty-text">暂无文档</div>
                    <button class="btn btn-primary" onclick="KnowledgePage.createNewDoc()">新建文档</button>
                </div>
            `;
            return;
        }

        const docsHtml = this.documents.map(doc => `
            <div class="doc-list-item" data-id="${doc.id}">
                <div class="doc-item-title">${doc.title}</div>
                <div class="doc-item-meta">
                    <span class="doc-tag doc-status-${doc.doc_status}">${this.getStatusText(doc.doc_status)}</span>
                    <span>📝 ${doc.author_name || '未知'}</span>
                    <span>👁️ ${doc.view_count || 0}</span>
                    <span>👍 ${doc.like_count || 0}</span>
                    <span>📅 ${this.formatDate(doc.update_time)}</span>
                    <span>🏷️ v${doc.version || '1.0'}</span>
                </div>
                ${doc.tags && doc.tags.length > 0 ? `
                    <div class="doc-item-tags">
                        ${doc.tags.map(tag => `<span class="doc-tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
                ${doc.highlight ? `
                    <div class="doc-item-highlight">...${doc.highlight}...</div>
                ` : ''}
            </div>
        `).join('');

        const totalPages = Math.ceil(this.total / this.pageSize) || 1;
        const paginationHtml = totalPages > 1 ? `
            <div class="pagination">
                <button class="pagination-btn" ${this.page <= 1 ? 'disabled' : ''} onclick="KnowledgePage.changePage(${this.page - 1})">上一页</button>
                <span class="pagination-info">${this.page} / ${totalPages}</span>
                <button class="pagination-btn" ${this.page >= totalPages ? 'disabled' : ''} onclick="KnowledgePage.changePage(${this.page + 1})">下一页</button>
            </div>
        ` : '';

        container.innerHTML = `
            <div class="doc-list">
                <div class="doc-list-header">
                    <span>共 ${this.total} 篇文档</span>
                </div>
                ${docsHtml}
                ${paginationHtml}
            </div>
        `;

        container.querySelectorAll('.doc-list-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = parseInt(item.dataset.id);
                this.openDocument(id);
            });
        });
    },

    changePage(page) {
        this.page = page;
        this.loadDocuments();
    },

    getStatusText(status) {
        const map = {
            draft: '草稿',
            published: '已发布',
            deprecated: '已废弃'
        };
        return map[status] || status;
    },

    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN');
    },

    // ==================== 文档详情 ====================

    async openDocument(docId) {
        try {
            const res = await KnowledgeService.getDocument(docId);
            if (res.code === 200) {
                this.currentDoc = res.data;
                this.view = 'detail';
                await KnowledgeService.recordView(docId);
                this.currentDoc.view_count = (this.currentDoc.view_count || 0) + 1;
                this.render();
                this.loadVersionHistory();
                this.loadComments();
            }
        } catch (e) {
            console.error('加载文档失败:', e);
            Toast.error('加载文档失败');
        }
    },

    async loadVersionHistory() {
        if (!this.currentDoc) return;
        try {
            const res = await KnowledgeService.getVersionHistory(this.currentDoc.id);
            if (res.code === 200) {
                this.versionHistory = res.data || [];
                this.renderVersionSelector();
            }
        } catch (e) {
            console.error('加载版本历史失败:', e);
        }
    },

    renderVersionSelector() {
        const versionSelect = document.getElementById('versionSelect');
        if (!versionSelect) return;

        const versions = this.versionHistory.length > 0 
            ? this.versionHistory 
            : [{ version: this.currentDoc.version, publish_time: this.currentDoc.update_time }];

        versionSelect.innerHTML = versions.map(v => `
            <option value="${v.id || ''}" ${v.version === this.currentDoc.version ? 'selected' : ''}>
                v${v.version} - ${this.formatDate(v.publish_time)}
            </option>
        `).join('');
    },

    async loadComments() {
        if (!this.currentDoc) return;
        try {
            const res = await KnowledgeService.getComments(this.currentDoc.id, { page: 1, size: 50 });
            if (res.code === 200) {
                this.comments = res.data.items || [];
                this.renderComments();
            }
        } catch (e) {
            console.error('加载评论失败:', e);
        }
    },

    renderDocDetail(container) {
        if (!this.currentDoc) return;

        const doc = this.currentDoc;
        const contentHtml = this.renderMarkdown(doc.content || '');

        container.innerHTML = `
            <div class="doc-detail">
                <div class="doc-detail-header">
                    <h1 class="doc-title">${doc.title}</h1>
                    <div class="doc-detail-meta">
                        <span class="doc-status-badge doc-status-${doc.doc_status}">${this.getStatusText(doc.doc_status)}</span>
                        <span>👤 ${doc.author_name || '未知作者'}</span>
                        <span>📅 ${this.formatDate(doc.update_time)}</span>
                        <span>👁️ ${doc.view_count || 0} 次浏览</span>
                        <span>🏷️ v${doc.version || '1.0'}</span>
                    </div>
                    ${doc.tags && doc.tags.length > 0 ? `
                        <div class="doc-tags">
                            ${doc.tags.map(tag => `<span class="doc-tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                    <div class="doc-actions-row">
                        <div class="version-selector">
                            <label>版本:</label>
                            <select id="versionSelect" class="form-input" style="width:auto;display:inline-block;">
                                <option value="">v${doc.version}</option>
                            </select>
                        </div>
                        <div class="like-section">
                            <button class="btn ${doc.has_liked ? 'btn-primary' : 'btn-outline'}" id="likeBtn">
                                👍 ${doc.like_count || 0}
                            </button>
                        </div>
                    </div>
                </div>

                <div class="doc-content markdown-body" id="docContent">
                    ${contentHtml}
                </div>

                ${doc.attachments ? `
                    <div class="doc-attachments">
                        <h4>📎 附件</h4>
                        <div class="attachment-list" id="attachmentList"></div>
                    </div>
                ` : ''}

                <div class="doc-comments-section">
                    <h4>💬 评论 (${this.comments.length})</h4>
                    <div class="comment-input-area">
                        <textarea class="form-input" id="commentInput" placeholder="写下你的评论..." rows="3"></textarea>
                        <button class="btn btn-primary" id="submitCommentBtn">发表评论</button>
                    </div>
                    <div class="comment-list" id="commentList"></div>
                </div>
            </div>
        `;

        this.bindDetailEvents();
        this.renderComments();
        this.renderAttachments();
    },

    bindDetailEvents() {
        document.getElementById('likeBtn')?.addEventListener('click', () => this.toggleLike());
        document.getElementById('submitCommentBtn')?.addEventListener('click', () => this.submitComment());
        document.getElementById('versionSelect')?.addEventListener('change', (e) => {
            const versionId = e.target.value;
            if (versionId) {
                this.rollbackVersion(parseInt(versionId));
            }
        });
    },

    renderAttachments() {
        const listEl = document.getElementById('attachmentList');
        if (!listEl || !this.currentDoc?.attachments) return;

        let attachments = [];
        try {
            attachments = typeof this.currentDoc.attachments === 'string'
                ? JSON.parse(this.currentDoc.attachments)
                : this.currentDoc.attachments;
        } catch (e) {
            attachments = [];
        }

        listEl.innerHTML = attachments.map((att, idx) => `
            <div class="attachment-item">
                <span>📎 ${att.name || `附件${idx + 1}`}</span>
                <button class="btn btn-sm btn-outline" onclick="KnowledgePage.downloadAttachment(${idx})">下载</button>
            </div>
        `).join('');
    },

    downloadAttachment(idx) {
        let attachments = [];
        try {
            attachments = typeof this.currentDoc.attachments === 'string'
                ? JSON.parse(this.currentDoc.attachments)
                : this.currentDoc.attachments;
        } catch (e) {
            return;
        }

        const att = attachments[idx];
        if (!att) return;

        const link = document.createElement('a');
        link.href = att.data || att.base64 || '';
        link.download = att.name || `attachment_${idx}`;
        link.click();
    },

    async toggleLike() {
        if (!this.currentDoc) return;
        try {
            const res = await KnowledgeService.toggleLike(this.currentDoc.id);
            if (res.code === 200) {
                this.currentDoc.has_liked = res.data.liked;
                this.currentDoc.like_count = res.data.like_count;
                const likeBtn = document.getElementById('likeBtn');
                if (likeBtn) {
                    likeBtn.className = `btn ${res.data.liked ? 'btn-primary' : 'btn-outline'}`;
                    likeBtn.innerHTML = `👍 ${res.data.like_count}`;
                }
            }
        } catch (e) {
            console.error('点赞失败:', e);
        }
    },

    async rollbackVersion(versionId) {
        const confirmed = await Modal.confirm('确定要回滚到该版本吗？当前内容将被替换。');
        if (!confirmed) {
            this.renderVersionSelector();
            return;
        }

        try {
            const res = await KnowledgeService.rollbackVersion(this.currentDoc.id, versionId);
            if (res.code === 200) {
                Toast.success('回滚成功');
                this.currentDoc = res.data;
                this.loadVersionHistory();
                this.renderDocDetail(document.getElementById('knowledgeContent'));
            } else {
                Toast.error(res.message || '回滚失败');
            }
        } catch (e) {
            Toast.error('回滚失败');
        }
    },

    // ==================== 评论 ====================

    renderComments() {
        const listEl = document.getElementById('commentList');
        if (!listEl) return;

        if (this.comments.length === 0) {
            listEl.innerHTML = '<div class="empty-comments">暂无评论，来发表第一条评论吧～</div>';
            return;
        }

        const renderComment = (comment, isReply = false) => `
            <div class="comment-item ${isReply ? 'comment-reply' : ''}" data-id="${comment.id}">
                <div class="comment-avatar">👤</div>
                <div class="comment-body">
                    <div class="comment-header">
                        <span class="comment-author">${comment.commenter_name || '匿名用户'}</span>
                        <span class="comment-time">${this.formatDate(comment.create_time)}</span>
                    </div>
                    <div class="comment-content">${comment.content}</div>
                    <div class="comment-actions">
                        <button class="comment-action-btn" data-action="reply" data-id="${comment.id}">
                            💬 回复
                        </button>
                    </div>
                    ${comment.replies && comment.replies.length > 0 ? `
                        <div class="comment-replies">
                            ${comment.replies.map(r => renderComment(r, true)).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        listEl.innerHTML = this.comments.map(c => renderComment(c)).join('');

        listEl.querySelectorAll('[data-action="reply"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const commentId = parseInt(btn.dataset.id);
                this.showReplyInput(commentId);
            });
        });
    },

    showReplyInput(commentId) {
        const commentEl = document.querySelector(`.comment-item[data-id="${commentId}"] .comment-body`);
        if (!commentEl) return;

        const existingInput = commentEl.querySelector('.reply-input-area');
        if (existingInput) {
            existingInput.remove();
            return;
        }

        const replyArea = document.createElement('div');
        replyArea.className = 'reply-input-area';
        replyArea.innerHTML = `
            <textarea class="form-input reply-input" placeholder="写下你的回复..." rows="2"></textarea>
            <button class="btn btn-sm btn-primary reply-submit-btn">回复</button>
            <button class="btn btn-sm btn-outline reply-cancel-btn">取消</button>
        `;

        commentEl.appendChild(replyArea);

        replyArea.querySelector('.reply-cancel-btn').addEventListener('click', () => {
            replyArea.remove();
        });

        replyArea.querySelector('.reply-submit-btn').addEventListener('click', async () => {
            const content = replyArea.querySelector('.reply-input').value.trim();
            if (!content) {
                Toast.warning('请输入回复内容');
                return;
            }

            try {
                const res = await KnowledgeService.createComment(this.currentDoc.id, {
                    content: content,
                    parent_id: commentId
                });
                if (res.code === 201) {
                    Toast.success('回复成功');
                    this.loadComments();
                } else {
                    Toast.error(res.message || '回复失败');
                }
            } catch (e) {
                Toast.error('回复失败');
            }
        });
    },

    async submitComment() {
        const input = document.getElementById('commentInput');
        const content = input?.value.trim();
        if (!content) {
            Toast.warning('请输入评论内容');
            return;
        }

        try {
            const res = await KnowledgeService.createComment(this.currentDoc.id, {
                content: content,
                parent_id: 0
            });
            if (res.code === 201) {
                Toast.success('评论成功');
                input.value = '';
                this.loadComments();
            } else {
                Toast.error(res.message || '评论失败');
            }
        } catch (e) {
            Toast.error('评论失败');
        }
    },

    // ==================== Markdown 渲染 ====================

    renderMarkdown(text) {
        if (!text) return '';
        if (window.marked) {
            return window.marked.parse(text);
        }
        return this.simpleMarkdown(text);
    },

    simpleMarkdown(text) {
        let html = text
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^\s*$/gm, '<br>')
            .replace(/\n/g, '<br>');
        return html;
    },

    // ==================== 文档编辑 ====================

    createNewDoc() {
        this.isCreating = true;
        this.editingDoc = {
            title: '',
            category_id: this.selectedCategoryId || (this.categoryTree[0]?.id),
            content: '',
            tags: [],
            version: '1.0',
            doc_status: 'draft',
            attachments: [],
            summary: ''
        };
        this.view = 'edit';
        this.render();
    },

    editCurrentDoc() {
        if (!this.currentDoc) return;
        this.isCreating = false;
        this.editingDoc = { ...this.currentDoc };
        if (!Array.isArray(this.editingDoc.tags)) {
            this.editingDoc.tags = [];
        }
        this.view = 'edit';
        this.render();
    },

    cancelEdit() {
        if (this.isCreating) {
            this.backToList();
        } else {
            this.view = 'detail';
            this.render();
        }
    },

    renderDocEdit(container) {
        const doc = this.editingDoc;
        const categories = this.flattenCategories();

        container.innerHTML = `
            <div class="doc-edit">
                <div class="doc-edit-header">
                    <input type="text" class="doc-title-input" id="docTitleInput" 
                        placeholder="请输入文档标题" value="${doc.title || ''}">
                </div>
                <div class="doc-edit-meta">
                    <div class="form-row">
                        <div class="form-group">
                            <label>所属分类</label>
                            <select class="form-input" id="docCategorySelect">
                                ${categories.map(c => `
                                    <option value="${c.id}" ${doc.category_id === c.id ? 'selected' : ''}>
                                        ${c.prefix}${c.name}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>版本号</label>
                            <input type="text" class="form-input" id="docVersionInput" 
                                value="${doc.version || '1.0'}">
                        </div>
                        <div class="form-group">
                            <label>状态</label>
                            <select class="form-input" id="docStatusSelect">
                                <option value="draft" ${doc.doc_status === 'draft' ? 'selected' : ''}>草稿</option>
                                <option value="published" ${doc.doc_status === 'published' ? 'selected' : ''}>发布</option>
                                <option value="deprecated" ${doc.doc_status === 'deprecated' ? 'selected' : ''}>废弃</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>标签（逗号分隔）</label>
                        <input type="text" class="form-input" id="docTagsInput" 
                            placeholder="标签1,标签2,标签3" 
                            value="${Array.isArray(doc.tags) ? doc.tags.join(',') : ''}">
                    </div>
                </div>
                <div class="doc-edit-body">
                    <div class="editor-panel">
                        <div class="panel-header">📝 编辑</div>
                        <textarea class="markdown-editor" id="markdownEditor" 
                            placeholder="在此输入 Markdown 内容...">${doc.content || ''}</textarea>
                    </div>
                    <div class="preview-panel">
                        <div class="panel-header">👁️ 预览</div>
                        <div class="markdown-preview markdown-body" id="markdownPreview"></div>
                    </div>
                </div>
                <div class="doc-edit-footer">
                    <div class="form-group">
                        <label>📎 附件上传</label>
                        <div class="attachment-upload-area">
                            <input type="file" id="attachmentInput" multiple style="display:none">
                            <button class="btn btn-outline" onclick="document.getElementById('attachmentInput').click()">
                                选择文件
                            </button>
                            <span class="upload-hint">支持多文件上传</span>
                            <div class="attachment-preview-list" id="attachmentPreviewList"></div>
                        </div>
                    </div>
                    <div class="edit-actions">
                        <button class="btn btn-outline" id="cancelEditBtn2">取消</button>
                        <button class="btn btn-primary" id="saveDocBtn2">保存文档</button>
                        ${doc.doc_status !== 'published' ? `
                            <button class="btn btn-success" id="publishDocBtn">发布文档</button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        this.bindEditEvents();
        this.updatePreview();
        this.renderAttachmentPreviews();
    },

    flattenCategories(items = this.categoryTree, prefix = '', result = []) {
        for (const item of items) {
            result.push({
                id: item.id,
                name: item.name,
                prefix: prefix
            });
            if (item.children?.length) {
                this.flattenCategories(item.children, prefix + '　', result);
            }
        }
        return result;
    },

    bindEditEvents() {
        const editor = document.getElementById('markdownEditor');
        editor?.addEventListener('input', () => {
            this.editingDoc.content = editor.value;
            this.updatePreview();
        });

        document.getElementById('cancelEditBtn2')?.addEventListener('click', () => this.cancelEdit());
        document.getElementById('saveDocBtn2')?.addEventListener('click', () => this.saveDocument());
        document.getElementById('publishDocBtn')?.addEventListener('click', () => this.publishDocument());

        document.getElementById('docTitleInput')?.addEventListener('input', (e) => {
            this.editingDoc.title = e.target.value;
        });
        document.getElementById('docCategorySelect')?.addEventListener('change', (e) => {
            this.editingDoc.category_id = parseInt(e.target.value);
        });
        document.getElementById('docVersionInput')?.addEventListener('input', (e) => {
            this.editingDoc.version = e.target.value;
        });
        document.getElementById('docStatusSelect')?.addEventListener('change', (e) => {
            this.editingDoc.doc_status = e.target.value;
        });
        document.getElementById('docTagsInput')?.addEventListener('input', (e) => {
            this.editingDoc.tags = e.target.value.split(',').map(t => t.trim()).filter(t => t);
        });

        const fileInput = document.getElementById('attachmentInput');
        fileInput?.addEventListener('change', (e) => this.handleAttachmentUpload(e));
    },

    handleAttachmentUpload(e) {
        const files = Array.from(e.target.files || []);
        if (!files.length) return;

        this.editingDoc.attachments = this.editingDoc.attachments || [];

        files.forEach(file => {
            const reader = new FileReader();
            reader.onload = (ev) => {
                this.editingDoc.attachments.push({
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    data: ev.target.result
                });
                this.renderAttachmentPreviews();
            };
            reader.readAsDataURL(file);
        });
    },

    renderAttachmentPreviews() {
        const listEl = document.getElementById('attachmentPreviewList');
        if (!listEl) return;

        const attachments = this.editingDoc.attachments || [];
        if (attachments.length === 0) {
            listEl.innerHTML = '';
            return;
        }

        listEl.innerHTML = attachments.map((att, idx) => `
            <div class="attachment-preview-item">
                <span>📎 ${att.name}</span>
                <button class="remove-attachment-btn" onclick="KnowledgePage.removeAttachment(${idx})">×</button>
            </div>
        `).join('');
    },

    removeAttachment(idx) {
        this.editingDoc.attachments.splice(idx, 1);
        this.renderAttachmentPreviews();
    },

    updatePreview() {
        const preview = document.getElementById('markdownPreview');
        if (preview) {
            preview.innerHTML = this.renderMarkdown(this.editingDoc.content || '');
        }
    },

    async saveDocument() {
        const title = document.getElementById('docTitleInput')?.value.trim();
        if (!title) {
            Toast.warning('请输入文档标题');
            return;
        }

        const data = {
            title: title,
            category_id: parseInt(document.getElementById('docCategorySelect')?.value) || this.categoryTree[0]?.id,
            content: this.editingDoc.content || '',
            tags: this.editingDoc.tags || [],
            version: document.getElementById('docVersionInput')?.value || '1.0',
            doc_status: document.getElementById('docStatusSelect')?.value || 'draft',
            attachments: this.editingDoc.attachments || []
        };

        try {
            let res;
            if (this.isCreating) {
                res = await KnowledgeService.createDocument(data);
                if (res.code === 201) {
                    Toast.success('创建成功');
                    this.currentDoc = res.data;
                    this.isCreating = false;
                    this.view = 'detail';
                    this.render();
                    this.loadDocuments();
                } else {
                    Toast.error(res.message || '创建失败');
                }
            } else {
                res = await KnowledgeService.updateDocument(this.currentDoc.id, data);
                if (res.code === 200) {
                    Toast.success('保存成功');
                    this.currentDoc = res.data;
                    this.view = 'detail';
                    this.render();
                    this.loadDocuments();
                } else {
                    Toast.error(res.message || '保存失败');
                }
            }
        } catch (e) {
            Toast.error('保存失败');
        }
    },

    async publishDocument() {
        const confirmed = await Modal.confirm('确定要发布这篇文档吗？');
        if (!confirmed) return;

        const title = document.getElementById('docTitleInput')?.value.trim();
        if (!title) {
            Toast.warning('请输入文档标题');
            return;
        }

        try {
            let docId;
            if (this.isCreating) {
                const data = {
                    title: title,
                    category_id: parseInt(document.getElementById('docCategorySelect')?.value) || this.categoryTree[0]?.id,
                    content: this.editingDoc.content || '',
                    tags: this.editingDoc.tags || [],
                    version: document.getElementById('docVersionInput')?.value || '1.0',
                    doc_status: 'draft',
                    attachments: this.editingDoc.attachments || []
                };
                const createRes = await KnowledgeService.createDocument(data);
                if (createRes.code !== 201) {
                    Toast.error(createRes.message || '创建失败');
                    return;
                }
                docId = createRes.data.id;
                this.currentDoc = createRes.data;
                this.isCreating = false;
            } else {
                docId = this.currentDoc.id;
            }

            const publishRes = await KnowledgeService.publishDocument(docId, {
                change_summary: '发布文档',
                version: document.getElementById('docVersionInput')?.value
            });

            if (publishRes.code === 200) {
                Toast.success('发布成功');
                this.currentDoc = publishRes.data;
                this.view = 'detail';
                this.render();
                this.loadDocuments();
            } else {
                Toast.error(publishRes.message || '发布失败');
            }
        } catch (e) {
            Toast.error('发布失败');
        }
    }
};

window.KnowledgePage = KnowledgePage;
