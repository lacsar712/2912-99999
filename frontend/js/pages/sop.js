/**
 * SOP标准作业管理页面
 */
const SOPPage = {
    activeTab: 'list',
    sops: [],
    versions: [],
    currentSOP: null,
    editingSOP: null,
    draftSteps: [],
    checklists: [],
    currentChecklist: null,
    complianceStats: null,
    equipments: [],
    trainingCourses: [],
    _activeModal: null,
    _diffData: null,
    _draggedIndex: null,

    init() {
        this.activeTab = 'list';
        this.render();
        this.loadEquipments();
        this.loadTrainingCourses();
        this.loadSOPs();
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

    getStatusBadge(status) {
        const map = {
            draft: { label: '草稿', style: 'background:#fff3cd;color:#856404;' },
            published: { label: '已发布', style: 'background:#d4edda;color:#155724;' },
            deprecated: { label: '已废弃', style: 'background:#f8d7da;color:#721c24;' }
        };
        const s = map[status] || { label: status, style: '' };
        return `<span class="status-badge" style="${s.style}">${s.label}</span>`;
    },

    async loadEquipments() {
        try {
            const res = await Request.get('/api/production/equipments', { size: 500 });
            if (res.code === 200) {
                this.equipments = res.data.items || [];
            }
        } catch (e) {}
    },

    async loadTrainingCourses() {
        try {
            const res = await TrainingService.getCourses({ size: 500 });
            if (res.code === 200) {
                this.trainingCourses = res.data.items || [];
            }
        } catch (e) {}
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">SOP标准作业管理</h3>
                </div>
                <div class="card-body">
                    <div class="safety-tab-bar">
                        <div class="safety-tab active" data-tab="list">SOP文档</div>
                        <div class="safety-tab" data-tab="checklist">执行检查表</div>
                        <div class="safety-tab" data-tab="stats">合规率看板</div>
                    </div>
                    <div id="sopTabContent"></div>
                </div>
            </div>
            <style>
                .sop-step-card { border:1px solid var(--border-color);border-radius:8px;padding:12px;margin-bottom:8px;background:white;cursor:grab;transition:all .2s; }
                .sop-step-card:hover { box-shadow:0 2px 8px rgba(0,0,0,.1); }
                .sop-step-card.dragging { opacity:.5; }
                .sop-step-card.drop-target { border-color:var(--primary-color);border-style:dashed; }
                .step-drag-handle { color:var(--text-muted);cursor:grab;margin-right:8px;user-select:none; }
                .diff-col { flex:1;min-width:0;overflow-y:auto;max-height:500px;padding:12px;border:1px solid var(--border-color);border-radius:6px; }
                .diff-col-left { background:#fff5f5; }
                .diff-col-right { background:#f0fff4; }
                .diff-removed { background:#fecaca;color:#7f1d1d;padding:2px 4px;border-radius:3px;text-decoration:line-through; }
                .diff-added { background:#bbf7d0;color:#14532d;padding:2px 4px;border-radius:3px; }
                .diff-unchanged { color:var(--text-secondary); }
                .checklist-item-card { border:1px solid var(--border-color);border-radius:8px;padding:16px;margin-bottom:12px;background:white;transition:all .2s; }
                .checklist-item-card.completed { border-color:#28a745;background:#f0fff4; }
                .photo-preview-box { width:100%;height:120px;border:2px dashed var(--border-color);border-radius:6px;display:flex;align-items:center;justify-content:center;cursor:pointer;overflow:hidden;background:var(--bg-light); }
                .photo-preview-box img { max-width:100%;max-height:100%; }
                .photo-preview-box.has-photo { border-style:solid; }
            </style>
        `;
        this._setupTabListeners();
        this._renderTabContent();
    },

    _setupTabListeners() {
        document.querySelectorAll('.safety-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.safety-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.activeTab = tab.dataset.tab;
                this._renderTabContent();
            });
        });
    },

    _renderTabContent() {
        switch (this.activeTab) {
            case 'list': this._renderListTab(); break;
            case 'checklist': this._renderChecklistTab(); break;
            case 'stats': this._renderStatsTab(); break;
        }
    },

    // ==================== Tab 1: SOP文档列表与编辑器 ====================

    async loadSOPs() {
        try {
            const res = await SOPService.getSOPs({ size: 200 });
            if (res.code === 200) {
                this.sops = res.data.items || [];
            }
        } catch (e) {
            Toast.error('加载SOP列表失败');
        }
        if (this.activeTab === 'list') {
            this._renderListTab();
        }
    },

    _renderListTab() {
        const content = document.getElementById('sopTabContent');
        if (this.editingSOP) {
            this._renderEditor(content);
            return;
        }
        if (this._diffData) {
            this._renderDiffViewer(content);
            return;
        }
        if (this.currentSOP) {
            this._renderSOPDetail(content);
            return;
        }
        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <select class="form-control" id="sopStatusFilter" style="width:120px;display:inline-block;">
                        <option value="">全部状态</option>
                        <option value="draft">草稿</option>
                        <option value="published">已发布</option>
                        <option value="deprecated">已废弃</option>
                    </select>
                    <input type="text" class="form-control" id="sopKeywordSearch" placeholder="搜索编号/名称" style="width:200px;display:inline-block;margin-left:8px;">
                    <button class="btn btn-outline" style="margin-left:8px;" onclick="SOPPage._applyFilter()">搜索</button>
                </div>
                <div>
                    <button class="btn btn-primary" id="addSOPBtn" onclick="SOPPage._openEditor()">+ 新建SOP</button>
                </div>
            </div>
            <div id="sopListWrap">
                ${this.sops.length === 0 ? '<div style="text-align:center;padding:40px;color:var(--text-secondary);">暂无SOP文档</div>' : `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>编号</th>
                            <th>名称</th>
                            <th>适用产品/工序</th>
                            <th>版本</th>
                            <th>状态</th>
                            <th>步骤数</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.sops.map(s => `
                            <tr>
                                <td>${s.sop_code || '-'}</td>
                                <td>${s.sop_name || '-'}</td>
                                <td>${s.applicable_product || '-'}</td>
                                <td>v${s.version || '1.0'}</td>
                                <td>${this.getStatusBadge(s.status)}</td>
                                <td>${s.step_count || 0}</td>
                                <td>${s.create_time ? s.create_time.substring(0, 16) : '-'}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline" onclick="SOPPage._viewSOP(${s.id})">查看</button>
                                    <button class="btn btn-sm btn-primary" onclick="SOPPage._openEditor(${s.id})">编辑</button>
                                    <button class="btn btn-sm btn-danger" onclick="SOPPage._deleteSOP(${s.id})">删除</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                `}
            </div>
        `;
    },

    _applyFilter() {
        const status = document.getElementById('sopStatusFilter').value;
        const keyword = document.getElementById('sopKeywordSearch').value.trim();
        SOPService.getSOPs({ size: 200, status, keyword }).then(res => {
            if (res.code === 200) {
                this.sops = res.data.items || [];
                this._renderListTab();
            }
        });
    },

    async _viewSOP(sopId) {
        try {
            const res = await SOPService.getSOP(sopId);
            if (res.code === 200) {
                this.currentSOP = res.data;
                this._renderListTab();
            }
        } catch (e) {
            Toast.error('加载SOP详情失败');
        }
    },

    _renderSOPDetail(content) {
        const s = this.currentSOP;
        content.innerHTML = `
            <div style="margin-bottom:16px;">
                <button class="btn btn-outline" onclick="SOPPage._backToList()">← 返回列表</button>
            </div>
            <div class="card" style="margin-bottom:16px;">
                <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h4 style="margin:0;">${s.sop_name}</h4>
                        <div style="font-size:13px;color:var(--text-secondary);margin-top:4px;">
                            编号: ${s.sop_code} | 版本: v${s.version} | ${this.getStatusBadge(s.status)}
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-outline" onclick="SOPPage._openEditor(${s.id})">编辑</button>
                        <button class="btn btn-success" onclick="SOPPage._openPublishModal(${s.id})" ${s.status === 'published' ? 'disabled' : ''}>发布新版本</button>
                        ${(s.versions && s.versions.length >= 2) ? `<button class="btn btn-outline" onclick="SOPPage._openDiffModal(${s.id})">查看版本差异</button>` : ''}
                    </div>
                </div>
                <div class="card-body">
                    <div style="margin-bottom:12px;"><strong>适用产品/工序:</strong> ${s.applicable_product || '-'}</div>
                    <div style="margin-bottom:12px;"><strong>关联设备:</strong> ${this._renderEquipmentNames(s.equipment_id_list)}</div>
                    <div style="margin-bottom:12px;"><strong>描述:</strong> ${s.description || '-'}</div>
                    <hr style="margin:16px 0;">
                    <h5>步骤列表 (${s.steps ? s.steps.length : 0})</h5>
                    ${(!s.steps || s.steps.length === 0) ? '<div style="color:var(--text-secondary);">暂无步骤</div>' : `
                    <div style="margin-top:12px;">
                        ${s.steps.map((st, idx) => `
                            <div style="border:1px solid var(--border-color);border-radius:8px;padding:12px;margin-bottom:8px;background:var(--bg-light);">
                                <div style="font-weight:600;margin-bottom:6px;">
                                    <span style="display:inline-block;width:24px;height:24px;background:var(--primary-color);color:white;border-radius:50%;text-align:center;line-height:24px;font-size:12px;margin-right:8px;">${idx + 1}</span>
                                    ${st.title}
                                    ${st.duration_minutes ? `<span style="color:var(--text-secondary);font-weight:normal;font-size:12px;margin-left:8px;">预计 ${st.duration_minutes} 分钟</span>` : ''}
                                </div>
                                ${st.description ? `<div style="color:var(--text-secondary);margin:6px 0 6px 32px;">${st.description}</div>` : ''}
                                ${st.image_base64 ? `<div style="margin-left:32px;"><img src="data:image/jpeg;base64,${st.image_base64}" style="max-width:200px;max-height:150px;border-radius:4px;border:1px solid var(--border-color);"></div>` : ''}
                                ${st.video_url ? `<div style="margin-left:32px;"><a href="${st.video_url}" target="_blank">📹 查看视频</a></div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                    `}
                    ${(s.versions && s.versions.length > 0) ? `
                    <hr style="margin:20px 0;">
                    <h5>版本历史</h5>
                    <table class="data-table" style="margin-top:12px;">
                        <thead><tr><th>版本</th><th>变更说明</th><th>发布时间</th></tr></thead>
                        <tbody>
                            ${s.versions.map(v => `
                                <tr>
                                    <td>v${v.version}</td>
                                    <td>${v.change_log || '-'}</td>
                                    <td>${v.published_time ? v.published_time.substring(0, 16) : '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    ` : ''}
                    ${(s.training_relations && s.training_relations.length > 0) ? `
                    <hr style="margin:20px 0;">
                    <h5>关联培训课程</h5>
                    <div style="margin-top:8px;">
                        ${s.training_relations.map(r => `
                            <span class="doc-tag" style="margin-right:6px;margin-bottom:4px;">${r.course_code || ''} - ${r.course_name || ''}</span>
                        `).join('')}
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    },

    _renderEquipmentNames(ids) {
        if (!ids || ids.length === 0) return '-';
        return ids.map(id => {
            const eq = this.equipments.find(e => e.id === id);
            return eq ? `${eq.equipment_code}-${eq.equipment_name}` : `ID:${id}`;
        }).join(', ');
    },

    _backToList() {
        this.currentSOP = null;
        this.editingSOP = null;
        this._diffData = null;
        this._renderListTab();
    },

    async _deleteSOP(sopId) {
        const confirmed = await Modal.confirm('确定要删除该SOP文档吗？');
        if (!confirmed) return;
        try {
            const res = await SOPService.deleteSOP(sopId);
            if (res.code === 200) {
                Toast.success('删除成功');
                this.loadSOPs();
            } else {
                Toast.error(res.message || '删除失败');
            }
        } catch (e) {
            Toast.error('删除失败');
        }
    },

    _openEditor(sopId) {
        if (sopId) {
            SOPService.getSOP(sopId).then(res => {
                if (res.code === 200) {
                    const s = res.data;
                    this.editingSOP = {
                        id: s.id,
                        sop_code: s.sop_code,
                        sop_name: s.sop_name,
                        applicable_product: s.applicable_product,
                        version: s.version,
                        status: s.status,
                        description: s.description,
                        equipment_id_list: s.equipment_id_list || [],
                        steps: (s.steps || []).map((st, idx) => ({
                            id: st.id,
                            order: st.step_order || idx + 1,
                            title: st.title,
                            description: st.description,
                            image_base64: st.image_base64,
                            video_url: st.video_url,
                            duration_minutes: st.duration_minutes || 0
                        }))
                    };
                    this._renderListTab();
                }
            });
        } else {
            this.editingSOP = {
                id: null,
                sop_code: '',
                sop_name: '',
                applicable_product: '',
                version: '1.0',
                status: 'draft',
                description: '',
                equipment_id_list: [],
                steps: []
            };
            this._renderListTab();
        }
    },

    _renderEditor(content) {
        const s = this.editingSOP;
        content.innerHTML = `
            <div style="margin-bottom:16px;">
                <button class="btn btn-outline" onclick="SOPPage._cancelEdit()">← 取消编辑</button>
            </div>
            <div class="card">
                <div class="card-header"><h4>${s.id ? '编辑' : '新建'} SOP</h4></div>
                <div class="card-body">
                    <div class="form-row">
                        <div class="form-group">
                            <label>SOP编号 *</label>
                            <input type="text" class="form-input" id="editSopCode" value="${s.sop_code}" placeholder="如: SOP-001">
                        </div>
                        <div class="form-group">
                            <label>版本号</label>
                            <input type="text" class="form-input" id="editVersion" value="${s.version}" placeholder="1.0">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>SOP名称 *</label>
                            <input type="text" class="form-input" id="editSopName" value="${s.sop_name}" placeholder="请输入SOP名称">
                        </div>
                        <div class="form-group">
                            <label>状态</label>
                            <select class="form-input" id="editStatus">
                                <option value="draft" ${s.status === 'draft' ? 'selected' : ''}>草稿</option>
                                <option value="published" ${s.status === 'published' ? 'selected' : ''}>已发布</option>
                                <option value="deprecated" ${s.status === 'deprecated' ? 'selected' : ''}>已废弃</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>适用产品/工序</label>
                            <input type="text" class="form-input" id="editProduct" value="${s.applicable_product || ''}" placeholder="如: 汽车发动机装配">
                        </div>
                        <div class="form-group">
                            <label>关联设备 (可多选)</label>
                            <select class="form-input" id="editEquipments" multiple style="min-height:80px;">
                                ${this.equipments.map(e => `
                                    <option value="${e.id}" ${(s.equipment_id_list || []).includes(e.id) ? 'selected' : ''}>${e.equipment_code} - ${e.equipment_name}</option>
                                `).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>SOP描述</label>
                        <textarea class="form-input" id="editDescription" rows="3" placeholder="简要描述该SOP的用途和范围">${s.description || ''}</textarea>
                    </div>

                    <hr style="margin:20px 0;">

                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                        <h5 style="margin:0;">步骤列表 (可拖拽排序)</h5>
                        <button class="btn btn-outline btn-sm" onclick="SOPPage._addStep()">+ 添加步骤</button>
                    </div>
                    <div id="stepEditorList">
                        ${(s.steps || []).length === 0 ? '<div style="text-align:center;padding:24px;color:var(--text-secondary);border:2px dashed var(--border-color);border-radius:8px;">暂无步骤，点击上方按钮添加</div>' : ''}
                    </div>

                    <div style="margin-top:20px;text-align:right;">
                        <button class="btn btn-outline" onclick="SOPPage._cancelEdit()">取消</button>
                        <button class="btn btn-primary" onclick="SOPPage._saveSOP()" style="margin-left:8px;">保存</button>
                    </div>
                </div>
            </div>
        `;
        this._renderStepCards();
    },

    _renderStepCards() {
        const list = document.getElementById('stepEditorList');
        if (!list) return;
        const steps = this.editingSOP.steps || [];
        if (steps.length === 0) {
            list.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-secondary);border:2px dashed var(--border-color);border-radius:8px;">暂无步骤，点击上方按钮添加</div>';
            return;
        }
        list.innerHTML = steps.map((st, idx) => `
            <div class="sop-step-card" draggable="true" data-index="${idx}" id="stepCard-${idx}">
                <div style="display:flex;align-items:flex-start;gap:8px;">
                    <span class="step-drag-handle" title="拖拽排序">⋮⋮</span>
                    <div style="flex:1;min-width:0;">
                        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
                            <span style="display:inline-block;width:24px;height:24px;background:var(--primary-color);color:white;border-radius:50%;text-align:center;line-height:24px;font-size:12px;flex-shrink:0;">${idx + 1}</span>
                            <input type="text" class="form-input" placeholder="步骤标题" style="flex:1;min-width:200px;" value="${st.title || ''}" onchange="SOPPage._updateStepField(${idx}, 'title', this.value)">
                            <input type="number" class="form-input" placeholder="时长(分钟)" style="width:100px;" value="${st.duration_minutes || ''}" onchange="SOPPage._updateStepField(${idx}, 'duration_minutes', parseInt(this.value) || 0)">
                            <button class="btn btn-sm btn-danger" onclick="SOPPage._removeStep(${idx})">删除</button>
                        </div>
                        <textarea class="form-input" placeholder="步骤描述" rows="2" style="margin-bottom:8px;" onchange="SOPPage._updateStepField(${idx}, 'description', this.value)">${st.description || ''}</textarea>
                        <input type="text" class="form-input" placeholder="视频URL (可选)" style="margin-bottom:8px;" value="${st.video_url || ''}" onchange="SOPPage._updateStepField(${idx}, 'video_url', this.value)">
                        <div style="display:flex;gap:12px;align-items:flex-start;">
                            <div style="flex:1;">
                                <label style="font-size:12px;color:var(--text-secondary);">步骤图片 (可选)</label>
                                <div class="photo-preview-box ${st.image_base64 ? 'has-photo' : ''}" onclick="document.getElementById('stepImageInput-${idx}').click()">
                                    ${st.image_base64 ? `<img src="data:image/jpeg;base64,${st.image_base64}">` : '<span style="color:var(--text-muted);">点击上传图片</span>'}
                                </div>
                                <input type="file" id="stepImageInput-${idx}" accept="image/*" style="display:none;" onchange="SOPPage._handleStepImage(${idx}, this)">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        list.querySelectorAll('.sop-step-card').forEach(card => {
            card.addEventListener('dragstart', (e) => {
                this._draggedIndex = parseInt(card.dataset.index);
                card.classList.add('dragging');
            });
            card.addEventListener('dragend', () => {
                card.classList.remove('dragging');
                this._draggedIndex = null;
                list.querySelectorAll('.sop-step-card').forEach(c => c.classList.remove('drop-target'));
            });
            card.addEventListener('dragover', (e) => {
                e.preventDefault();
                card.classList.add('drop-target');
            });
            card.addEventListener('dragleave', () => {
                card.classList.remove('drop-target');
            });
            card.addEventListener('drop', (e) => {
                e.preventDefault();
                card.classList.remove('drop-target');
                const targetIdx = parseInt(card.dataset.index);
                if (this._draggedIndex !== null && this._draggedIndex !== targetIdx) {
                    const steps = this.editingSOP.steps;
                    const [removed] = steps.splice(this._draggedIndex, 1);
                    steps.splice(targetIdx, 0, removed);
                    steps.forEach((s, i) => s.order = i + 1);
                    this._renderStepCards();
                }
            });
        });
    },

    _addStep() {
        const steps = this.editingSOP.steps || [];
        steps.push({
            order: steps.length + 1,
            title: '',
            description: '',
            image_base64: '',
            video_url: '',
            duration_minutes: 0
        });
        this._renderStepCards();
    },

    _removeStep(idx) {
        this.editingSOP.steps.splice(idx, 1);
        this.editingSOP.steps.forEach((s, i) => s.order = i + 1);
        this._renderStepCards();
    },

    _updateStepField(idx, field, value) {
        this.editingSOP.steps[idx][field] = value;
    },

    _handleStepImage(idx, input) {
        const file = input.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64 = e.target.result.split(',')[1];
            this.editingSOP.steps[idx].image_base64 = base64;
            this._renderStepCards();
        };
        reader.readAsDataURL(file);
    },

    _cancelEdit() {
        this.editingSOP = null;
        this._renderListTab();
    },

    async _saveSOP() {
        const data = {
            sop_code: document.getElementById('editSopCode').value.trim(),
            sop_name: document.getElementById('editSopName').value.trim(),
            applicable_product: document.getElementById('editProduct').value.trim(),
            version: document.getElementById('editVersion').value.trim(),
            status: document.getElementById('editStatus').value,
            description: document.getElementById('editDescription').value.trim(),
            equipment_id_list: Array.from(document.getElementById('editEquipments').selectedOptions).map(o => parseInt(o.value)),
            steps: (this.editingSOP.steps || []).map((s, i) => ({
                order: i + 1,
                title: s.title,
                description: s.description,
                image_base64: s.image_base64,
                video_url: s.video_url,
                duration_minutes: s.duration_minutes
            }))
        };
        if (!data.sop_code || !data.sop_name) {
            Toast.warning('请填写必填项：编号和名称');
            return;
        }
        try {
            const res = this.editingSOP.id
                ? await SOPService.updateSOP(this.editingSOP.id, data)
                : await SOPService.createSOP(data);
            if (res.code === 200 || res.code === 201) {
                Toast.success('保存成功');
                this.editingSOP = null;
                this.loadSOPs();
            } else {
                Toast.error(res.message || '保存失败');
            }
        } catch (e) {
            Toast.error('保存失败');
        }
    },

    _openPublishModal(sopId) {
        this.openModal({
            title: '发布新版本',
            content: `
                <div style="padding:8px 0;">
                    <div class="form-group">
                        <label>版本号 (留空自动递增)</label>
                        <input type="text" class="form-input" id="publishVersion" placeholder="如: 1.1">
                    </div>
                    <div class="form-group">
                        <label>变更说明</label>
                        <textarea class="form-input" id="publishChangeLog" rows="3" placeholder="请描述本次变更的内容"></textarea>
                    </div>
                </div>
            `,
            buttons: [
                { text: '取消', className: 'btn-outline', onClick: () => this.closeModal() },
                { text: '发布', className: 'btn-primary', onClick: () => this._doPublish(sopId) }
            ]
        });
    },

    async _doPublish(sopId) {
        const data = {
            version: document.getElementById('publishVersion').value.trim() || null,
            change_log: document.getElementById('publishChangeLog').value.trim()
        };
        try {
            const res = await SOPService.publishSOP(sopId, data);
            if (res.code === 200) {
                Toast.success('发布成功');
                this.closeModal();
                this.loadSOPs();
                this._viewSOP(sopId);
            } else {
                Toast.error(res.message || '发布失败');
            }
        } catch (e) {
            Toast.error('发布失败');
        }
    },

    _openDiffModal(sopId) {
        SOPService.getSOP(sopId).then(res => {
            if (res.code !== 200) return;
            const versions = res.data.versions || [];
            const opts = versions.map(v => `<option value="${v.id}">v${v.version} (${v.published_time ? v.published_time.substring(0, 16) : ''})</option>`).join('');
            this.openModal({
                title: '版本差异对比',
                content: `
                    <div style="padding:8px 0;">
                        <div class="form-row">
                            <div class="form-group">
                                <label>旧版本</label>
                                <select class="form-input" id="diffV1">${versions.slice(1).map((v, i) => `<option value="${v.id}">v${v.version}</option>`).join('')}</select>
                            </div>
                            <div class="form-group">
                                <label>新版本</label>
                                <select class="form-input" id="diffV2">${versions.map((v, i) => `<option value="${v.id}" ${i === 0 ? 'selected' : ''}>v${v.version}</option>`).join('')}</select>
                            </div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="SOPPage._doLoadDiff(${sopId})">对比</button>
                    </div>
                    <div id="diffResultArea" style="margin-top:16px;"></div>
                `,
                buttons: [
                    { text: '关闭', className: 'btn-outline', onClick: () => this.closeModal() }
                ],
                width: '900px'
            });
        });
    },

    async _doLoadDiff(sopId) {
        const v1 = parseInt(document.getElementById('diffV1').value);
        const v2 = parseInt(document.getElementById('diffV2').value);
        try {
            const res = await SOPService.getVersionDiff(sopId, { version1_id: v1, version2_id: v2 });
            if (res.code === 200) {
                this._diffData = res.data;
                this._renderDiffResult();
            }
        } catch (e) {
            Toast.error('加载差异失败');
        }
    },

    _renderDiffResult() {
        const area = document.getElementById('diffResultArea');
        if (!area || !this._diffData) return;
        const d = this._diffData;
        if (!d.has_diff) {
            area.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-secondary);">两个版本无差异</div>';
            return;
        }
        let html = `<div style="display:flex;gap:12px;align-items:stretch;">
            <div class="diff-col diff-col-left">
                <div style="font-weight:600;margin-bottom:8px;color:#7f1d1d;">旧版本: v${d.version1.version}</div>`;
        d.fields.forEach(f => {
            html += `<div style="margin-bottom:8px;"><strong>${f.field}:</strong> <span class="diff-removed">${f.old || '(空)'}</span></div>`;
        });
        d.steps.removed.forEach(s => {
            html += `<div style="margin-bottom:8px;padding:8px;background:#fecaca;border-radius:4px;"><strong>删除步骤 ${s.order}:</strong> ${s.step.title}</div>`;
        });
        d.steps.modified.forEach(m => {
            html += `<div style="margin-bottom:8px;padding:8px;background:#fff3cd;border-radius:4px;"><strong>修改步骤 ${m.order}:</strong><br>`;
            Object.keys(m.fields).forEach(k => {
                html += `${k}: <span class="diff-removed">${m.fields[k].old || '(空)'}</span><br>`;
            });
            html += `</div>`;
        });
        d.steps.unchanged.forEach(u => {
            html += `<div style="margin-bottom:4px;color:var(--text-secondary);">步骤 ${u.order}: ${u.step.title}</div>`;
        });
        html += `</div><div class="diff-col diff-col-right">
            <div style="font-weight:600;margin-bottom:8px;color:#14532d;">新版本: v${d.version2.version}</div>`;
        d.fields.forEach(f => {
            html += `<div style="margin-bottom:8px;"><strong>${f.field}:</strong> <span class="diff-added">${f.new || '(空)'}</span></div>`;
        });
        d.steps.added.forEach(s => {
            html += `<div style="margin-bottom:8px;padding:8px;background:#bbf7d0;border-radius:4px;"><strong>新增步骤 ${s.order}:</strong> ${s.step.title}</div>`;
        });
        d.steps.modified.forEach(m => {
            html += `<div style="margin-bottom:8px;padding:8px;background:#d4edda;border-radius:4px;"><strong>修改步骤 ${m.order}:</strong><br>`;
            Object.keys(m.fields).forEach(k => {
                html += `${k}: <span class="diff-added">${m.fields[k].new || '(空)'}</span><br>`;
            });
            html += `</div>`;
        });
        d.steps.unchanged.forEach(u => {
            html += `<div style="margin-bottom:4px;color:var(--text-secondary);">步骤 ${u.order}: ${u.step.title}</div>`;
        });
        html += `</div></div>`;
        area.innerHTML = html;
    },

    // ==================== Tab 2: 执行检查表 ====================

    async loadChecklists() {
        try {
            const res = await SOPService.getChecklists({ size: 200 });
            if (res.code === 200) {
                this.checklists = res.data.items || [];
            }
        } catch (e) {}
    },

    async _renderChecklistTab() {
        await this.loadChecklists();
        const content = document.getElementById('sopTabContent');
        if (this.currentChecklist) {
            this._renderChecklistDetail(content);
            return;
        }
        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">
                <div style="color:var(--text-secondary);font-size:13px;">操作员视角 - 按步骤逐条勾选并拍照留证</div>
                <button class="btn btn-primary" onclick="SOPPage._openNewChecklistModal()">+ 新建执行检查</button>
            </div>
            ${this.checklists.length === 0 ? '<div style="text-align:center;padding:40px;color:var(--text-secondary);">暂无执行记录</div>' : `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>SOP</th>
                        <th>版本</th>
                        <th>设备</th>
                        <th>操作员</th>
                        <th>合规率</th>
                        <th>开始时间</th>
                        <th>签到人/时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.checklists.map(c => `
                        <tr>
                            <td>${c.sop_code || ''} ${c.sop_name || ''}</td>
                            <td>v${c.sop_version || '-'}</td>
                            <td>${c.equipment_name || '-'}</td>
                            <td>${c.operator_name || '-'}</td>
                            <td>
                                <span class="status-badge" style="background:${(c.compliance_rate >= 100) ? 'rgba(40,167,69,.1);color:#28a745' : (c.compliance_rate >= 60 ? 'rgba(255,193,7,.1);color:#856404' : 'rgba(220,53,69,.1);color:#dc3545')};">
                                    ${c.compliance_rate != null ? c.compliance_rate + '%' : '-'}
                                </span>
                            </td>
                            <td>${c.start_time ? c.start_time.substring(0, 16) : '-'}</td>
                            <td>${c.signer_name || '-'} ${c.sign_time ? '(' + c.sign_time.substring(0, 16) + ')' : ''}</td>
                            <td>
                                ${c.sign_time ? '' : `<button class="btn btn-sm btn-primary" onclick="SOPPage._openChecklist(${c.id})">执行</button>`}
                                <button class="btn btn-sm btn-outline" onclick="SOPPage._viewChecklist(${c.id})">查看</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            `}
        `;
    },

    _openNewChecklistModal() {
        const sopOpts = this.sops.filter(s => s.status === 'published').map(s => `<option value="${s.id}">${s.sop_code} - ${s.sop_name} (v${s.version})</option>`).join('');
        const eqOpts = this.equipments.map(e => `<option value="${e.id}">${e.equipment_code} - ${e.equipment_name}</option>`).join('');
        this.openModal({
            title: '新建执行检查',
            content: `
                <div style="padding:8px 0;">
                    <div class="form-group">
                        <label>选择SOP *</label>
                        <select class="form-input" id="newClSop">${sopOpts}</select>
                    </div>
                    <div class="form-group">
                        <label>选择设备</label>
                        <select class="form-input" id="newClEq"><option value="">-- 无 --</option>${eqOpts}</select>
                    </div>
                    <div class="form-group">
                        <label>操作员姓名</label>
                        <input type="text" class="form-input" id="newClOperator" placeholder="请输入操作员姓名">
                    </div>
                </div>
            `,
            buttons: [
                { text: '取消', className: 'btn-outline', onClick: () => this.closeModal() },
                { text: '开始执行', className: 'btn-primary', onClick: () => this._createChecklist() }
            ]
        });
    },

    async _createChecklist() {
        const data = {
            sop_id: parseInt(document.getElementById('newClSop').value),
            equipment_id: parseInt(document.getElementById('newClEq').value) || null,
            operator_name: document.getElementById('newClOperator').value.trim()
        };
        if (!data.sop_id) {
            Toast.warning('请选择SOP');
            return;
        }
        try {
            const res = await SOPService.createChecklist(data);
            if (res.code === 201) {
                Toast.success('创建成功');
                this.closeModal();
                this._openChecklist(res.data.id);
            } else {
                Toast.error(res.message || '创建失败');
            }
        } catch (e) {
            Toast.error('创建失败');
        }
    },

    async _openChecklist(id) {
        try {
            const res = await SOPService.getChecklist(id);
            if (res.code === 200) {
                this.currentChecklist = res.data;
                this._renderChecklistTab();
            }
        } catch (e) {
            Toast.error('加载失败');
        }
    },

    async _viewChecklist(id) {
        try {
            const res = await SOPService.getChecklist(id);
            if (res.code === 200) {
                this.currentChecklist = res.data;
                this._renderChecklistTab();
            }
        } catch (e) {
            Toast.error('加载失败');
        }
    },

    _renderChecklistDetail(content) {
        const c = this.currentChecklist;
        const isSubmitted = !!c.sign_time;
        const items = c.items || [];
        const completed = items.filter(i => i.is_completed).length;
        const rate = items.length ? Math.round(completed / items.length * 100) : 0;
        content.innerHTML = `
            <div style="margin-bottom:16px;">
                <button class="btn btn-outline" onclick="SOPPage._backToChecklistList()">← 返回列表</button>
            </div>
            <div class="card" style="margin-bottom:16px;">
                <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h4 style="margin:0;">${c.sop_name || ''}</h4>
                        <div style="font-size:13px;color:var(--text-secondary);margin-top:4px;">
                            版本: v${c.sop_version} | 设备: ${c.equipment_name || '-'} | 操作员: ${c.operator_name || '-'}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:24px;font-weight:600;color:${rate >= 100 ? '#28a745' : (rate >= 60 ? '#ffc107' : '#dc3545')};">${rate}%</div>
                        <div style="font-size:12px;color:var(--text-secondary);">进度 ${completed}/${items.length}</div>
                    </div>
                </div>
                <div class="card-body">
                    ${items.map((it, idx) => `
                        <div class="checklist-item-card ${it.is_completed ? 'completed' : ''}" id="clItem-${idx}">
                            <div style="display:flex;gap:12px;align-items:flex-start;">
                                <div style="flex-shrink:0;padding-top:2px;">
                                    <input type="checkbox" ${it.is_completed ? 'checked' : ''} ${isSubmitted ? 'disabled' : ''}
                                        style="width:20px;height:20px;cursor:pointer;"
                                        onchange="SOPPage._toggleCheckItem(${c.id}, ${it.id}, ${idx}, this.checked)">
                                </div>
                                <div style="flex:1;min-width:0;">
                                    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
                                        <div style="font-weight:600;">
                                            <span style="display:inline-block;width:24px;height:24px;background:var(--primary-color);color:white;border-radius:50%;text-align:center;line-height:24px;font-size:12px;margin-right:8px;">${idx + 1}</span>
                                            ${it.step_title || ''}
                                        </div>
                                        ${it.completed_time ? `<span style="font-size:12px;color:var(--text-secondary);">完成于 ${it.completed_time.substring(0, 16)}</span>` : ''}
                                    </div>
                                    ${it.step_description ? `<div style="color:var(--text-secondary);margin:6px 0 8px 32px;">${it.step_description}</div>` : ''}
                                    <div style="margin-left:32px;display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;">
                                        <div style="min-width:200px;flex:1;max-width:300px;">
                                            <label style="font-size:12px;color:var(--text-secondary);">现场照片${isSubmitted ? '' : ' (点击上传)'}</label>
                                            <div class="photo-preview-box ${it.photo_base64 ? 'has-photo' : ''}" ${isSubmitted ? '' : `onclick="document.getElementById('clPhotoInput-${idx}').click()"`}>
                                                ${it.photo_base64 ? `<img src="data:image/jpeg;base64,${it.photo_base64}">` : (isSubmitted ? '<span style="color:var(--text-muted);">无</span>' : '<span style="color:var(--text-muted);">点击上传照片</span>')}
                                            </div>
                                            ${isSubmitted ? '' : `<input type="file" id="clPhotoInput-${idx}" accept="image/*" style="display:none;" onchange="SOPPage._handleChecklistPhoto(${c.id}, ${it.id}, ${idx}, this)">`}
                                        </div>
                                        <div style="flex:1;min-width:200px;">
                                            <label style="font-size:12px;color:var(--text-secondary);">备注</label>
                                            <textarea class="form-input" rows="2" ${isSubmitted ? 'disabled' : ''}
                                                placeholder="可添加备注"
                                                onchange="SOPPage._updateChecklistRemark(${c.id}, ${it.id}, ${idx}, this.value)">${it.remark || ''}</textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ${isSubmitted ? `
                <div class="card">
                    <div class="card-body" style="text-align:center;">
                        <div style="font-size:16px;margin-bottom:8px;">✅ 已提交签到</div>
                        <div style="color:var(--text-secondary);">签到人: ${c.signer_name || '-'} | 签到时间: ${c.sign_time ? c.sign_time.substring(0, 16) : '-'}</div>
                        ${c.remark ? `<div style="margin-top:8px;">备注: ${c.remark}</div>` : ''}
                    </div>
                </div>
            ` : `
                <div style="text-align:right;">
                    <button class="btn btn-outline" onclick="SOPPage._backToChecklistList()">暂存返回</button>
                    <button class="btn btn-success" style="margin-left:8px;" onclick="SOPPage._openSubmitChecklistModal(${c.id})">提交签到 (${completed}/${items.length})</button>
                </div>
            `}
        `;
    },

    async _toggleCheckItem(checklistId, itemId, idx, checked) {
        try {
            const res = await SOPService.updateChecklistItem(checklistId, itemId, { is_completed: checked });
            if (res.code === 200) {
                const card = document.getElementById(`clItem-${idx}`);
                if (checked) card?.classList.add('completed'); else card?.classList.remove('completed');
                await this._refreshChecklist(checklistId);
            }
        } catch (e) {
            Toast.error('操作失败');
        }
    },

    _handleChecklistPhoto(checklistId, itemId, idx, input) {
        const file = input.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64 = e.target.result.split(',')[1];
            try {
                const res = await SOPService.updateChecklistItem(checklistId, itemId, { photo_base64: base64 });
                if (res.code === 200) {
                    Toast.success('照片已上传');
                    await this._refreshChecklist(checklistId);
                }
            } catch (err) {
                Toast.error('上传失败');
            }
        };
        reader.readAsDataURL(file);
    },

    async _updateChecklistRemark(checklistId, itemId, idx, value) {
        try {
            await SOPService.updateChecklistItem(checklistId, itemId, { remark: value });
        } catch (e) {}
    },

    async _refreshChecklist(id) {
        try {
            const res = await SOPService.getChecklist(id);
            if (res.code === 200) {
                this.currentChecklist = res.data;
                const c = this.currentChecklist;
                const items = c.items || [];
                const completed = items.filter(i => i.is_completed).length;
                const rate = items.length ? Math.round(completed / items.length * 100) : 0;
                const header = document.querySelector('.card-header h4');
                if (header) {
                    const parent = header.parentElement.parentElement;
                    const rateDiv = parent.querySelector('div[style*="text-align:right"]');
                    if (rateDiv) {
                        rateDiv.innerHTML = `
                            <div style="font-size:24px;font-weight:600;color:${rate >= 100 ? '#28a745' : (rate >= 60 ? '#ffc107' : '#dc3545')};">${rate}%</div>
                            <div style="font-size:12px;color:var(--text-secondary);">进度 ${completed}/${items.length}</div>
                        `;
                    }
                }
            }
        } catch (e) {}
    },

    _openSubmitChecklistModal(checklistId) {
        const user = AuthService.getCurrentUser();
        this.openModal({
            title: '提交签到',
            content: `
                <div style="padding:8px 0;">
                    <div class="form-group">
                        <label>签到人姓名</label>
                        <input type="text" class="form-input" id="submitSigner" value="${user?.username || ''}" placeholder="请输入签到人姓名">
                    </div>
                    <div class="form-group">
                        <label>备注 (可选)</label>
                        <textarea class="form-input" id="submitRemark" rows="2"></textarea>
                    </div>
                </div>
            `,
            buttons: [
                { text: '取消', className: 'btn-outline', onClick: () => this.closeModal() },
                { text: '确认提交', className: 'btn-success', onClick: () => this._doSubmitChecklist(checklistId) }
            ]
        });
    },

    async _doSubmitChecklist(checklistId) {
        const data = {
            signer_name: document.getElementById('submitSigner').value.trim(),
            remark: document.getElementById('submitRemark').value.trim()
        };
        if (!data.signer_name) {
            Toast.warning('请输入签到人姓名');
            return;
        }
        try {
            const res = await SOPService.submitChecklist(checklistId, data);
            if (res.code === 200) {
                Toast.success('提交成功');
                this.closeModal();
                this._openChecklist(checklistId);
            } else {
                Toast.error(res.message || '提交失败');
            }
        } catch (e) {
            Toast.error('提交失败');
        }
    },

    _backToChecklistList() {
        this.currentChecklist = null;
        this._renderChecklistTab();
    },

    // ==================== Tab 3: 合规率看板 ====================

    async _renderStatsTab() {
        if (!this.complianceStats) {
            await this._loadStats();
        }
        const content = document.getElementById('sopTabContent');
        const s = this.complianceStats || {};
        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div style="display:flex;gap:8px;align-items:center;">
                    <label style="font-size:13px;color:var(--text-secondary);">开始日期:</label>
                    <input type="date" class="form-control" id="statStartDate" style="display:inline-block;width:150px;">
                    <label style="font-size:13px;color:var(--text-secondary);">结束日期:</label>
                    <input type="date" class="form-control" id="statEndDate" style="display:inline-block;width:150px;">
                    <button class="btn btn-outline btn-sm" onclick="SOPPage._loadStats()">查询</button>
                </div>
            </div>
            <div class="stat-cards">
                <div class="stat-card">
                    <div class="stat-card-icon primary">📋</div>
                    <div>
                        <div class="stat-card-title">总执行次数</div>
                        <div class="stat-card-value">${s.total_checklists || 0}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon success">✅</div>
                    <div>
                        <div class="stat-card-title">平均合规率</div>
                        <div class="stat-card-value">${s.avg_compliance_rate || 0}%</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon success">💯</div>
                    <div>
                        <div class="stat-card-title">完全合规</div>
                        <div class="stat-card-value">${s.compliant_count || 0}</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-icon warning">⚠️</div>
                    <div>
                        <div class="stat-card-title">存在不合规</div>
                        <div class="stat-card-value">${s.non_compliant_count || 0}</div>
                    </div>
                </div>
            </div>

            <div style="margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <div class="card">
                    <div class="card-header"><h4>按SOP统计</h4></div>
                    <div class="card-body">
                        ${(!s.by_sop || s.by_sop.length === 0) ? '<div style="color:var(--text-secondary);text-align:center;padding:20px;">暂无数据</div>' : `
                        <table class="data-table">
                            <thead><tr><th>SOP</th><th>执行次数</th><th>平均合规率</th></tr></thead>
                            <tbody>
                                ${s.by_sop.map(x => `
                                    <tr>
                                        <td>${x.sop_code || ''} ${x.sop_name || ''}</td>
                                        <td>${x.count}</td>
                                        <td><span style="color:${x.avg_rate >= 100 ? '#28a745' : (x.avg_rate >= 60 ? '#ffc107' : '#dc3545')};font-weight:600;">${x.avg_rate}%</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                        `}
                    </div>
                </div>
                <div class="card">
                    <div class="card-header"><h4>按设备统计</h4></div>
                    <div class="card-body">
                        ${(!s.by_equipment || s.by_equipment.length === 0) ? '<div style="color:var(--text-secondary);text-align:center;padding:20px;">暂无数据</div>' : `
                        <table class="data-table">
                            <thead><tr><th>设备</th><th>执行次数</th><th>平均合规率</th></tr></thead>
                            <tbody>
                                ${s.by_equipment.map(x => `
                                    <tr>
                                        <td>${x.equipment_name || (x.equipment_id ? 'ID:' + x.equipment_id : '-')}</td>
                                        <td>${x.count}</td>
                                        <td><span style="color:${x.avg_rate >= 100 ? '#28a745' : (x.avg_rate >= 60 ? '#ffc107' : '#dc3545')};font-weight:600;">${x.avg_rate}%</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                        `}
                    </div>
                </div>
            </div>

            <div class="card" style="margin-top:16px;">
                <div class="card-header"><h4>每日趋势</h4></div>
                <div class="card-body" style="min-height:200px;">
                    <canvas id="complianceTrendChart"></canvas>
                </div>
            </div>
        `;
        setTimeout(() => this._renderTrendChart(s.daily_trend || []), 100);
    },

    async _loadStats() {
        const params = {};
        const sd = document.getElementById('statStartDate')?.value;
        const ed = document.getElementById('statEndDate')?.value;
        if (sd) params.start_date = sd;
        if (ed) params.end_date = ed;
        try {
            const res = await SOPService.getComplianceStats(params);
            if (res.code === 200) {
                this.complianceStats = res.data;
            }
        } catch (e) {
            Toast.error('加载统计失败');
        }
    },

    _renderTrendChart(data) {
        const canvas = document.getElementById('complianceTrendChart');
        if (!canvas || typeof Chart === 'undefined') return;
        const labels = data.map(d => d.date);
        const values = data.map(d => d.avg_rate);
        const counts = data.map(d => d.count);
        new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: '平均合规率 (%)',
                        data: values,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40,167,69,.1)',
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: '执行次数',
                        data: counts,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0,123,255,.1)',
                        fill: false,
                        tension: 0.3,
                        yAxisID: 'y1',
                        type: 'bar'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, max: 100, position: 'left', title: { display: true, text: '合规率(%)' } },
                    y1: { beginAtZero: true, position: 'right', title: { display: true, text: '次数' }, grid: { drawOnChartArea: false } }
                }
            }
        });
    }
};

window.SOPPage = SOPPage;
