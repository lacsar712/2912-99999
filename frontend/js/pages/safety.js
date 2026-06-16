/**
 * 安全管理页面
 */
const SafetyPage = {
    activeTab: 'hazards',
    hazardTypes: [],
    hazards: [],
    accidents: [],
    reportData: null,
    charts: {},
    _activeModal: null,

    init() {
        this.activeTab = 'hazards';
        this.loadHazardTypes();
        this.render();
        this.loadTabData();
        this.startOverdueCheck();
    },

    destroy() {
        Object.values(this.charts).forEach(c => { if (c) c.destroy(); });
        this.charts = {};
        if (this._overdueInterval) clearInterval(this._overdueInterval);
    },

    startOverdueCheck() {
        this._overdueInterval = setInterval(() => {
            SafetyService.checkOverdue().catch(() => {});
        }, 60000);
    },

    async loadHazardTypes() {
        try {
            const res = await SafetyService.getHazardTypes({ size: 100 });
            if (res.code === 200) {
                this.hazardTypes = res.data.items || [];
            }
        } catch (e) {
            console.error('Load hazard types failed:', e);
        }
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

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">安全管理</h3>
                </div>
                <div class="card-body">
                    <div class="safety-tab-bar">
                        <div class="safety-tab active" data-tab="hazards">隐患看板</div>
                        <div class="safety-tab" data-tab="accidents">事故登记</div>
                        <div class="safety-tab" data-tab="report">月度安全报表</div>
                        <div class="safety-tab" data-tab="types">隐患类型管理</div>
                        <div class="safety-tab" data-tab="tasks">排查任务</div>
                    </div>
                    <div id="safetyTabContent"></div>
                </div>
            </div>
        `;
        this.setupTabListeners();
    },

    setupTabListeners() {
        document.querySelectorAll('.safety-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.safety-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.activeTab = tab.dataset.tab;
                this.loadTabData();
            });
        });
    },

    async loadTabData() {
        switch (this.activeTab) {
            case 'hazards': await this.loadHazards(); break;
            case 'accidents': await this.loadAccidents(); break;
            case 'report': await this.loadReport(); break;
            case 'types': await this.loadTypesTab(); break;
            case 'tasks': await this.loadTasksTab(); break;
        }
    },

    async loadHazards() {
        try {
            const res = await SafetyService.getHazardRecords({ size: 200 });
            if (res.code === 200) {
                this.hazards = res.data.items || [];
            }
        } catch (e) {
            Toast.error('加载隐患数据失败');
        }
        this.renderKanban();
    },

    renderKanban() {
        const content = document.getElementById('safetyTabContent');
        const columns = [
            { key: 'pending', label: '待整改', cls: 'pending' },
            { key: 'rectifying', label: '整改中', cls: 'rectifying' },
            { key: 'rectified', label: '已整改', cls: 'rectified' },
            { key: 'accepted', label: '已验收', cls: 'accepted' }
        ];
        const grouped = {};
        columns.forEach(c => grouped[c.key] = []);
        this.hazards.forEach(h => {
            if (grouped[h.hazard_status]) grouped[h.hazard_status].push(h);
            else grouped['pending'].push(h);
        });

        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <select class="form-control" id="hazardSeverityFilter" style="width:120px;display:inline-block;">
                        <option value="">全部严重程度</option>
                        <option value="low">低</option>
                        <option value="medium">中</option>
                        <option value="high">高</option>
                        <option value="critical">严重</option>
                    </select>
                    <select class="form-control" id="hazardTypeFilter" style="width:140px;display:inline-block;margin-left:8px;">
                        <option value="">全部类型</option>
                        ${this.hazardTypes.map(t => `<option value="${t.id}">${t.type_name}</option>`).join('')}
                    </select>
                </div>
                <button class="btn btn-primary" id="addHazardBtn">+ 录入隐患</button>
            </div>
            <div class="kanban-board">
                ${columns.map(col => `
                    <div class="kanban-column">
                        <div class="kanban-column-header ${col.cls}">
                            <span>${col.label}</span>
                            <span style="background:white;border-radius:10px;padding:1px 8px;font-size:12px;">${grouped[col.key].length}</span>
                        </div>
                        <div class="kanban-cards" data-status="${col.key}">
                            ${grouped[col.key].map(h => this.renderKanbanCard(h)).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        document.getElementById('addHazardBtn')?.addEventListener('click', () => this.showHazardForm());
        document.getElementById('hazardSeverityFilter')?.addEventListener('change', () => this.filterHazards());
        document.getElementById('hazardTypeFilter')?.addEventListener('change', () => this.filterHazards());
        content.querySelectorAll('.kanban-card').forEach(card => {
            card.addEventListener('click', () => this.showHazardDetail(parseInt(card.dataset.id)));
        });
    },

    renderKanbanCard(h) {
        const sevMap = { low: '低', medium: '中', high: '高', critical: '严重' };
        const overdue = h.deadline && new Date(h.deadline) < new Date() && (h.hazard_status === 'pending' || h.hazard_status === 'rectifying');
        return `
            <div class="kanban-card" data-id="${h.id}">
                <div class="kanban-card-title">${h.title || h.hazard_code}</div>
                <div class="kanban-card-meta">
                    <span class="badge-severity ${h.severity}">${sevMap[h.severity] || h.severity}</span>
                    ${h.hazard_type_name ? `<span style="margin-left:6px;">${h.hazard_type_name}</span>` : ''}
                </div>
                <div class="kanban-card-meta" style="margin-top:4px;">
                    ${h.location ? `📍 ${h.location}` : ''}
                    ${h.discoverer ? ` | 👤 ${h.discoverer}` : ''}
                </div>
                ${overdue ? '<div style="color:#dc3545;font-size:11px;margin-top:4px;">⚠️ 已超期</div>' : ''}
                ${h.is_escalated ? '<div style="color:#dc3545;font-size:11px;margin-top:2px;">🔔 已升级告警</div>' : ''}
            </div>
        `;
    },

    async filterHazards() {
        const severity = document.getElementById('hazardSeverityFilter')?.value;
        const typeId = document.getElementById('hazardTypeFilter')?.value;
        try {
            const res = await SafetyService.getHazardRecords({
                size: 200,
                severity: severity || undefined,
                hazardTypeId: typeId || undefined
            });
            if (res.code === 200) {
                this.hazards = res.data.items || [];
                this.renderKanban();
            }
        } catch (e) {
            Toast.error('筛选失败');
        }
    },

    showHazardForm(existingHazard) {
        const isEdit = !!existingHazard;
        const title = isEdit ? '编辑隐患' : '录入隐患';
        const h = existingHazard || {};
        this._pendingPhotoBase64 = null;
        this.openModal({
            title: title,
            width: '600px',
            content: `
                <form id="hazardForm">
                    <div class="form-group">
                        <label>隐患标题 *</label>
                        <input type="text" class="form-control" name="title" value="${h.title || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>发现人</label>
                        <input type="text" class="form-control" name="discoverer" value="${h.discoverer || ''}">
                    </div>
                    <div class="form-group">
                        <label>地点/设备</label>
                        <input type="text" class="form-control" name="location" value="${h.location || ''}">
                    </div>
                    <div class="form-group">
                        <label>隐患类型</label>
                        <select class="form-control" name="hazard_type_id">
                            <option value="">请选择</option>
                            ${this.hazardTypes.map(t => `<option value="${t.id}" ${h.hazard_type_id == t.id ? 'selected' : ''}>${t.type_name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>严重程度</label>
                        <select class="form-control" name="severity">
                            <option value="low" ${h.severity === 'low' ? 'selected' : ''}>低</option>
                            <option value="medium" ${h.severity === 'medium' || !h.severity ? 'selected' : ''}>中</option>
                            <option value="high" ${h.severity === 'high' ? 'selected' : ''}>高</option>
                            <option value="critical" ${h.severity === 'critical' ? 'selected' : ''}>严重</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>整改截止时间</label>
                        <input type="datetime-local" class="form-control" name="deadline" value="${h.deadline ? h.deadline.replace(' ', 'T').substring(0, 16) : ''}">
                    </div>
                    <div class="form-group">
                        <label>隐患描述</label>
                        <textarea class="form-control" name="description" rows="3">${h.description || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>现场照片</label>
                        <input type="file" accept="image/*" id="hazardPhotoInput" class="form-control">
                        <div id="hazardPhotoPreview" style="margin-top:8px;">
                            ${h.photo_base64 ? `<img src="data:image/jpeg;base64,${h.photo_base64}" class="photo-preview">` : ''}
                        </div>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('hazardForm');
                const data = {
                    title: form.title.value,
                    discoverer: form.discoverer.value,
                    location: form.location.value,
                    hazard_type_id: form.hazard_type_id.value ? parseInt(form.hazard_type_id.value) : null,
                    severity: form.severity.value,
                    description: form.description.value,
                    photo_base64: this._pendingPhotoBase64 || h.photo_base64 || null
                };
                if (form.deadline.value) {
                    data.deadline = form.deadline.value.replace('T', ' ') + ':00';
                }
                if (!data.title) {
                    Toast.error('请填写隐患标题');
                    return false;
                }
                try {
                    let res;
                    if (isEdit) {
                        res = await SafetyService.updateHazardRecord(h.id, data);
                    } else {
                        res = await SafetyService.createHazardRecord(data);
                    }
                    if (res.code === 200 || res.code === 201) {
                        Toast.show(isEdit ? '更新成功' : '创建成功', 'success');
                        this.loadHazards();
                        return true;
                    } else {
                        Toast.error(res.message);
                        return false;
                    }
                } catch (e) {
                    Toast.error('操作失败');
                    return false;
                }
            }
        });
        setTimeout(() => {
            const photoInput = document.getElementById('hazardPhotoInput');
            if (photoInput) {
                photoInput.addEventListener('change', (e) => this.handlePhotoUpload(e, 'hazardPhotoPreview', '_pendingPhotoBase64'));
            }
        }, 100);
    },

    handlePhotoUpload(e, previewId, storageKey) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            const base64 = ev.target.result.split(',')[1];
            this[storageKey] = base64;
            const preview = document.getElementById(previewId);
            if (preview) {
                preview.innerHTML = `<img src="${ev.target.result}" class="photo-preview">`;
            }
        };
        reader.readAsDataURL(file);
    },

    async showHazardDetail(id) {
        try {
            const res = await SafetyService.getHazardRecord(id);
            if (res.code !== 200) { Toast.error('获取详情失败'); return; }
            const h = res.data;
            const sevMap = { low: '低', medium: '中', high: '高', critical: '严重' };
            const statusMap = { pending: '待整改', rectifying: '整改中', rectified: '已整改', accepted: '已验收' };

            let actions = '';
            if (h.hazard_status === 'pending') {
                actions = `<button class="btn btn-primary" id="startRectBtn">开始整改</button>`;
            } else if (h.hazard_status === 'rectifying') {
                actions = `<button class="btn btn-success" id="addRectBtn">提交整改</button>`;
            } else if (h.hazard_status === 'rectified') {
                actions = `<button class="btn btn-info" id="acceptBtn">验收通过</button>`;
            }
            actions += ` <button class="btn btn-outline" id="editHazardBtn">编辑</button>`;

            const rectifications = h.rectifications || [];
            const rectHtml = rectifications.length > 0 ? `
                <h4 style="margin:16px 0 8px;">整改记录</h4>
                ${rectifications.map(r => `
                    <div style="background:var(--bg-light,#f8f9fa);padding:12px;border-radius:6px;margin-bottom:8px;">
                        <div><strong>措施：</strong>${r.measure}</div>
                        <div style="font-size:12px;color:var(--text-secondary,#6c757d);">
                            责任人: ${r.responsible_person || '-'} |
                            计划完成: ${r.plan_complete_time || '-'} |
                            实际完成: ${r.actual_complete_time || '-'}
                        </div>
                        ${r.photo_base64 ? `<img src="data:image/jpeg;base64,${r.photo_base64}" class="photo-preview" style="margin-top:8px;">` : ''}
                    </div>
                `).join('')}
            ` : '';

            this.openModal({
                title: `隐患详情 - ${h.hazard_code}`,
                width: '650px',
                content: `
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                        <div><strong>标题：</strong>${h.title}</div>
                        <div><strong>状态：</strong>${statusMap[h.hazard_status] || h.hazard_status}</div>
                        <div><strong>严重程度：</strong><span class="badge-severity ${h.severity}">${sevMap[h.severity]}</span></div>
                        <div><strong>隐患类型：</strong>${h.hazard_type_name || '-'}</div>
                        <div><strong>发现人：</strong>${h.discoverer || '-'}</div>
                        <div><strong>地点/设备：</strong>${h.location || '-'}</div>
                        <div><strong>整改截止：</strong>${h.deadline || '-'}</div>
                        <div><strong>是否升级：</strong>${h.is_escalated ? '是' : '否'}</div>
                    </div>
                    ${h.description ? `<div style="margin-top:12px;"><strong>描述：</strong>${h.description}</div>` : ''}
                    ${h.photo_base64 ? `<div style="margin-top:12px;"><strong>现场照片：</strong><br><img src="data:image/jpeg;base64,${h.photo_base64}" class="photo-preview"></div>` : ''}
                    ${rectHtml}
                    <div style="margin-top:16px;text-align:right;">${actions}</div>
                `,
                showFooter: false
            });

            setTimeout(() => {
                document.getElementById('startRectBtn')?.addEventListener('click', () => {
                    this.closeModal();
                    this.updateHazardStatus(id, 'rectifying');
                });
                document.getElementById('addRectBtn')?.addEventListener('click', () => {
                    this.closeModal();
                    this.showRectificationForm(id);
                });
                document.getElementById('acceptBtn')?.addEventListener('click', async () => {
                    this.closeModal();
                    try {
                        const res = await SafetyService.acceptHazard(id);
                        if (res.code === 200) {
                            Toast.show('验收通过', 'success');
                            this.loadHazards();
                        } else {
                            Toast.error(res.message);
                        }
                    } catch (e) { Toast.error('操作失败'); }
                });
                document.getElementById('editHazardBtn')?.addEventListener('click', () => {
                    this.closeModal();
                    this.showHazardForm(h);
                });
            }, 100);
        } catch (e) {
            Toast.error('获取详情失败');
        }
    },

    async updateHazardStatus(id, status) {
        try {
            const res = await SafetyService.updateHazardRecord(id, { hazard_status: status });
            if (res.code === 200) {
                Toast.show('状态已更新', 'success');
                this.loadHazards();
            } else {
                Toast.error(res.message);
            }
        } catch (e) { Toast.error('操作失败'); }
    },

    showRectificationForm(hazardId) {
        this._pendingRectPhotoBase64 = null;
        this.openModal({
            title: '提交整改',
            width: '600px',
            content: `
                <form id="rectForm">
                    <div class="form-group">
                        <label>整改措施 *</label>
                        <textarea class="form-control" name="measure" rows="3" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>整改责任人</label>
                        <input type="text" class="form-control" name="responsible_person">
                    </div>
                    <div class="form-group">
                        <label>计划完成时间</label>
                        <input type="datetime-local" class="form-control" name="plan_complete_time">
                    </div>
                    <div class="form-group">
                        <label>实际完成时间</label>
                        <input type="datetime-local" class="form-control" name="actual_complete_time">
                    </div>
                    <div class="form-group">
                        <label>整改结果</label>
                        <textarea class="form-control" name="result" rows="2"></textarea>
                    </div>
                    <div class="form-group">
                        <label>整改后照片</label>
                        <input type="file" accept="image/*" id="rectPhotoInput" class="form-control">
                        <div id="rectPhotoPreview" style="margin-top:8px;"></div>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('rectForm');
                const data = {
                    hazard_id: hazardId,
                    measure: form.measure.value,
                    responsible_person: form.responsible_person.value,
                    result: form.result.value,
                    photo_base64: this._pendingRectPhotoBase64 || null
                };
                if (form.plan_complete_time.value) {
                    data.plan_complete_time = form.plan_complete_time.value.replace('T', ' ') + ':00';
                }
                if (form.actual_complete_time.value) {
                    data.actual_complete_time = form.actual_complete_time.value.replace('T', ' ') + ':00';
                }
                if (!data.measure) {
                    Toast.error('请填写整改措施');
                    return false;
                }
                try {
                    const res = await SafetyService.createRectificationRecord(data);
                    if (res.code === 200 || res.code === 201) {
                        Toast.show('整改已提交', 'success');
                        this.loadHazards();
                        return true;
                    } else {
                        Toast.error(res.message);
                        return false;
                    }
                } catch (e) { Toast.error('提交失败'); return false; }
            }
        });
        setTimeout(() => {
            const photoInput = document.getElementById('rectPhotoInput');
            if (photoInput) {
                photoInput.addEventListener('change', (e) => this.handlePhotoUpload(e, 'rectPhotoPreview', '_pendingRectPhotoBase64'));
            }
        }, 100);
    },

    async loadAccidents() {
        try {
            const res = await SafetyService.getAccidentRecords({ size: 100 });
            if (res.code === 200) {
                this.accidents = res.data.items || [];
            }
        } catch (e) {
            Toast.error('加载事故数据失败');
        }
        this.renderAccidents();
    },

    renderAccidents() {
        const content = document.getElementById('safetyTabContent');
        const sevMap = { minor: '一般', general: '普通', major: '重大', critical: '特别重大' };
        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;">
                <div>
                    <select class="form-control" id="accidentSeverityFilter" style="width:140px;display:inline-block;">
                        <option value="">全部等级</option>
                        <option value="minor">一般</option>
                        <option value="general">普通</option>
                        <option value="major">重大</option>
                        <option value="critical">特别重大</option>
                    </select>
                </div>
                <button class="btn btn-primary" id="addAccidentBtn">+ 登记事故</button>
            </div>
            <div id="accidentsTableWrap">
                ${this.accidents.length === 0 ? '<div style="text-align:center;padding:40px;color:var(--text-secondary);">暂无事故记录</div>' : `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>事故编号</th>
                            <th>事故时间</th>
                            <th>地点</th>
                            <th>涉及人员</th>
                            <th>等级</th>
                            <th>损失估计(元)</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.accidents.map(a => `
                            <tr>
                                <td>${a.accident_code || '-'}</td>
                                <td>${a.accident_time || '-'}</td>
                                <td>${a.location || '-'}</td>
                                <td>${a.involved_persons || '-'}</td>
                                <td><span class="badge-severity ${a.severity === 'minor' ? 'low' : a.severity === 'general' ? 'medium' : a.severity === 'major' ? 'high' : 'critical'}">${sevMap[a.severity] || a.severity}</span></td>
                                <td>${a.loss_estimate != null ? parseFloat(a.loss_estimate).toLocaleString() : '-'}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline" onclick="SafetyPage.showAccidentDetail(${a.id})">查看</button>
                                    <button class="btn btn-sm btn-outline" onclick="SafetyPage.editAccident(${a.id})">编辑</button>
                                    <button class="btn btn-sm btn-danger" onclick="SafetyPage.deleteAccident(${a.id})">删除</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                `}
            </div>
        `;
        document.getElementById('addAccidentBtn')?.addEventListener('click', () => this.showAccidentForm());
        document.getElementById('accidentSeverityFilter')?.addEventListener('change', () => this.filterAccidents());
    },

    async filterAccidents() {
        const severity = document.getElementById('accidentSeverityFilter')?.value;
        try {
            const res = await SafetyService.getAccidentRecords({ severity: severity || undefined, size: 100 });
            if (res.code === 200) {
                this.accidents = res.data.items || [];
                this.renderAccidents();
            }
        } catch (e) { Toast.error('筛选失败'); }
    },

    showAccidentForm(existingAccident) {
        const isEdit = !!existingAccident;
        const a = existingAccident || {};
        this._pendingAccidentFileBase64 = null;
        this.openModal({
            title: isEdit ? '编辑事故' : '登记事故',
            width: '600px',
            content: `
                <form id="accidentForm">
                    <div class="form-group">
                        <label>事故时间 *</label>
                        <input type="datetime-local" class="form-control" name="accident_time" value="${a.accident_time ? a.accident_time.replace(' ', 'T').substring(0, 16) : ''}" required>
                    </div>
                    <div class="form-group">
                        <label>事故地点 *</label>
                        <input type="text" class="form-control" name="location" value="${a.location || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>事故等级</label>
                        <select class="form-control" name="severity">
                            <option value="minor" ${a.severity === 'minor' ? 'selected' : ''}>一般</option>
                            <option value="general" ${a.severity === 'general' || !a.severity ? 'selected' : ''}>普通</option>
                            <option value="major" ${a.severity === 'major' ? 'selected' : ''}>重大</option>
                            <option value="critical" ${a.severity === 'critical' ? 'selected' : ''}>特别重大</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>涉及人员</label>
                        <input type="text" class="form-control" name="involved_persons" value="${a.involved_persons || ''}">
                    </div>
                    <div class="form-group">
                        <label>损失估计(元)</label>
                        <input type="number" class="form-control" name="loss_estimate" step="0.01" value="${a.loss_estimate || ''}">
                    </div>
                    <div class="form-group">
                        <label>事故描述</label>
                        <textarea class="form-control" name="description" rows="3">${a.description || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>原因分析</label>
                        <textarea class="form-control" name="cause_analysis" rows="3">${a.cause_analysis || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>整改措施</label>
                        <textarea class="form-control" name="rectification_measures" rows="3">${a.rectification_measures || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>附件(图片)</label>
                        <input type="file" accept="image/*" id="accidentFileInput" class="form-control">
                        <div id="accidentFilePreview" style="margin-top:8px;">
                            ${a.attachment_base64 ? `<img src="data:image/jpeg;base64,${a.attachment_base64}" class="photo-preview">` : ''}
                        </div>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('accidentForm');
                const data = {
                    accident_time: form.accident_time.value.replace('T', ' ') + ':00',
                    location: form.location.value,
                    severity: form.severity.value,
                    involved_persons: form.involved_persons.value,
                    loss_estimate: form.loss_estimate.value || null,
                    description: form.description.value,
                    cause_analysis: form.cause_analysis.value,
                    rectification_measures: form.rectification_measures.value,
                    attachment_base64: this._pendingAccidentFileBase64 || a.attachment_base64 || null
                };
                if (!data.location || !data.accident_time) {
                    Toast.error('请填写事故时间和地点');
                    return false;
                }
                try {
                    let res;
                    if (isEdit) {
                        res = await SafetyService.updateAccidentRecord(a.id, data);
                    } else {
                        res = await SafetyService.createAccidentRecord(data);
                    }
                    if (res.code === 200 || res.code === 201) {
                        Toast.show(isEdit ? '更新成功' : '登记成功', 'success');
                        this.loadAccidents();
                        return true;
                    } else {
                        Toast.error(res.message);
                        return false;
                    }
                } catch (e) { Toast.error('操作失败'); return false; }
            }
        });
        setTimeout(() => {
            const fileInput = document.getElementById('accidentFileInput');
            if (fileInput) {
                fileInput.addEventListener('change', (e) => this.handlePhotoUpload(e, 'accidentFilePreview', '_pendingAccidentFileBase64'));
            }
        }, 100);
    },

    async showAccidentDetail(id) {
        try {
            const res = await SafetyService.getAccidentRecord(id);
            if (res.code !== 200) { Toast.error('获取详情失败'); return; }
            const a = res.data;
            const sevMap = { minor: '一般', general: '普通', major: '重大', critical: '特别重大' };
            this.openModal({
                title: `事故详情 - ${a.accident_code}`,
                width: '600px',
                content: `
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                        <div><strong>事故时间：</strong>${a.accident_time || '-'}</div>
                        <div><strong>地点：</strong>${a.location || '-'}</div>
                        <div><strong>等级：</strong>${sevMap[a.severity] || a.severity}</div>
                        <div><strong>涉及人员：</strong>${a.involved_persons || '-'}</div>
                        <div><strong>损失估计：</strong>${a.loss_estimate != null ? parseFloat(a.loss_estimate).toLocaleString() + ' 元' : '-'}</div>
                    </div>
                    ${a.description ? `<div style="margin-top:12px;"><strong>描述：</strong>${a.description}</div>` : ''}
                    ${a.cause_analysis ? `<div style="margin-top:8px;"><strong>原因分析：</strong>${a.cause_analysis}</div>` : ''}
                    ${a.rectification_measures ? `<div style="margin-top:8px;"><strong>整改措施：</strong>${a.rectification_measures}</div>` : ''}
                    ${a.attachment_base64 ? `<div style="margin-top:8px;"><strong>附件：</strong><br><img src="data:image/jpeg;base64,${a.attachment_base64}" class="photo-preview"></div>` : ''}
                `,
                showFooter: false
            });
        } catch (e) { Toast.error('获取详情失败'); }
    },

    async editAccident(id) {
        try {
            const res = await SafetyService.getAccidentRecord(id);
            if (res.code === 200) {
                this.showAccidentForm(res.data);
            }
        } catch (e) { Toast.error('获取数据失败'); }
    },

    async deleteAccident(id) {
        const confirmed = await Modal.confirm('确定要删除该事故记录吗？');
        if (!confirmed) return;
        try {
            const res = await SafetyService.deleteAccidentRecord(id);
            if (res.code === 200) {
                Toast.show('删除成功', 'success');
                this.loadAccidents();
            } else {
                Toast.error(res.message);
            }
        } catch (e) { Toast.error('删除失败'); }
    },

    async loadReport() {
        try {
            const res = await SafetyService.getMonthlyReport({ months: 6 });
            if (res.code === 200) {
                this.reportData = res.data;
            }
        } catch (e) {
            Toast.error('加载报表数据失败');
        }
        this.renderReport();
    },

    renderReport() {
        const content = document.getElementById('safetyTabContent');
        const data = this.reportData;
        if (!data) {
            content.innerHTML = '<div style="text-align:center;padding:40px;">加载中...</div>';
            return;
        }
        const summary = data.summary || {};
        const trend = data.trend || {};

        content.innerHTML = `
            <div class="grid grid-4" style="margin-bottom:24px;">
                <div class="stat-card" style="background:rgba(255,193,7,0.1);">
                    <div class="stat-card-title" style="color:#856404;">隐患总数</div>
                    <div class="stat-card-value" style="color:#856404;">${summary.total_hazards || 0}</div>
                </div>
                <div class="stat-card" style="background:rgba(40,167,69,0.1);">
                    <div class="stat-card-title" style="color:#155724;">整改率</div>
                    <div class="stat-card-value" style="color:#155724;">${summary.overall_rectification_rate || 0}%</div>
                </div>
                <div class="stat-card" style="background:rgba(220,53,69,0.1);">
                    <div class="stat-card-title" style="color:#721c24;">事故总数</div>
                    <div class="stat-card-value" style="color:#721c24;">${summary.total_accidents || 0}</div>
                </div>
                <div class="stat-card" style="background:rgba(23,162,184,0.1);">
                    <div class="stat-card-title" style="color:#004085;">待整改</div>
                    <div class="stat-card-value" style="color:#004085;">${summary.pending || 0}</div>
                </div>
            </div>
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">隐患与整改趋势</h3></div>
                    <div class="card-body"><canvas id="hazardTrendChart" height="250"></canvas></div>
                </div>
                <div class="card">
                    <div class="card-header"><h3 class="card-title">事故趋势</h3></div>
                    <div class="card-body"><canvas id="accidentTrendChart" height="250"></canvas></div>
                </div>
            </div>
            <div class="grid grid-2" style="margin-top:16px;">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">隐患严重程度分布</h3></div>
                    <div class="card-body"><canvas id="severityChart" height="250"></canvas></div>
                </div>
                <div class="card">
                    <div class="card-header"><h3 class="card-title">整改率趋势</h3></div>
                    <div class="card-body"><canvas id="rectRateChart" height="250"></canvas></div>
                </div>
            </div>
        `;

        setTimeout(() => this.renderCharts(), 100);
    },

    renderCharts() {
        const data = this.reportData;
        if (!data) return;
        const trend = data.trend || {};
        const bySeverity = data.by_severity || {};

        if (this.charts.hazardTrend) this.charts.hazardTrend.destroy();
        if (this.charts.accidentTrend) this.charts.accidentTrend.destroy();
        if (this.charts.severity) this.charts.severity.destroy();
        if (this.charts.rectRate) this.charts.rectRate.destroy();

        const labels = trend.labels || [];
        this.charts.hazardTrend = new Chart(document.getElementById('hazardTrendChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    { label: '隐患数', data: trend.hazard_counts || [], backgroundColor: 'rgba(255,193,7,0.7)' },
                    { label: '已整改数', data: trend.rectified_counts || [], backgroundColor: 'rgba(40,167,69,0.7)' }
                ]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        this.charts.accidentTrend = new Chart(document.getElementById('accidentTrendChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '事故数',
                    data: trend.accident_counts || [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220,53,69,0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        this.charts.severity = new Chart(document.getElementById('severityChart'), {
            type: 'bar',
            data: {
                labels: ['低', '中', '高', '严重'],
                datasets: [{
                    label: '隐患数',
                    data: [bySeverity.low || 0, bySeverity.medium || 0, bySeverity.high || 0, bySeverity.critical || 0],
                    backgroundColor: ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
                }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        this.charts.rectRate = new Chart(document.getElementById('rectRateChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '整改率(%)',
                    data: trend.rectification_rates || [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40,167,69,0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } }
        });
    },

    async loadTypesTab() {
        try {
            const res = await SafetyService.getHazardTypes({ size: 100 });
            if (res.code === 200) {
                this.hazardTypes = res.data.items || [];
            }
        } catch (e) { Toast.error('加载隐患类型失败'); }
        this.renderTypesTab();
    },

    renderTypesTab() {
        const content = document.getElementById('safetyTabContent');
        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;">
                <select class="form-control" id="typeCategoryFilter" style="width:160px;display:inline-block;">
                    <option value="">全部分类</option>
                    <option value="人员违规">人员违规</option>
                    <option value="设备隐患">设备隐患</option>
                    <option value="环境隐患">环境隐患</option>
                    <option value="消防隐患">消防隐患</option>
                </select>
                <button class="btn btn-primary" id="addHazardTypeBtn">+ 新增隐患类型</button>
            </div>
            <table class="data-table">
                <thead>
                    <tr><th>编码</th><th>名称</th><th>分类</th><th>描述</th><th>状态</th><th>操作</th></tr>
                </thead>
                <tbody>
                    ${this.hazardTypes.map(t => `
                        <tr>
                            <td>${t.type_code}</td>
                            <td>${t.type_name}</td>
                            <td>${t.category || '-'}</td>
                            <td>${t.description || '-'}</td>
                            <td>${t.is_active ? '<span class="badge badge-success">启用</span>' : '<span class="badge badge-danger">禁用</span>'}</td>
                            <td>
                                <button class="btn btn-sm btn-outline" onclick="SafetyPage.editHazardType(${t.id})">编辑</button>
                                <button class="btn btn-sm btn-danger" onclick="SafetyPage.deleteHazardType(${t.id})">删除</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.getElementById('addHazardTypeBtn')?.addEventListener('click', () => this.showHazardTypeForm());
        document.getElementById('typeCategoryFilter')?.addEventListener('change', async (e) => {
            const cat = e.target.value;
            try {
                const res = await SafetyService.getHazardTypes({ category: cat || undefined, size: 100 });
                if (res.code === 200) this.hazardTypes = res.data.items || [];
                this.renderTypesTab();
            } catch (e) { Toast.error('筛选失败'); }
        });
    },

    showHazardTypeForm(existingType) {
        const isEdit = !!existingType;
        const h = existingType || {};
        this.openModal({
            title: isEdit ? '编辑隐患类型' : '新增隐患类型',
            content: `
                <form id="htForm">
                    <div class="form-group">
                        <label>类型编码 *</label>
                        <input type="text" class="form-control" name="type_code" value="${h.type_code || ''}" ${isEdit ? 'readonly' : ''}>
                    </div>
                    <div class="form-group">
                        <label>类型名称 *</label>
                        <input type="text" class="form-control" name="type_name" value="${h.type_name || ''}">
                    </div>
                    <div class="form-group">
                        <label>分类</label>
                        <select class="form-control" name="category">
                            <option value="">请选择</option>
                            <option value="人员违规" ${h.category === '人员违规' ? 'selected' : ''}>人员违规</option>
                            <option value="设备隐患" ${h.category === '设备隐患' ? 'selected' : ''}>设备隐患</option>
                            <option value="环境隐患" ${h.category === '环境隐患' ? 'selected' : ''}>环境隐患</option>
                            <option value="消防隐患" ${h.category === '消防隐患' ? 'selected' : ''}>消防隐患</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>描述</label>
                        <textarea class="form-control" name="description" rows="2">${h.description || ''}</textarea>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('htForm');
                const data = {
                    type_code: form.type_code.value,
                    type_name: form.type_name.value,
                    category: form.category.value,
                    description: form.description.value
                };
                if (!data.type_code || !data.type_name) {
                    Toast.error('请填写编码和名称');
                    return false;
                }
                try {
                    let res;
                    if (isEdit) {
                        res = await SafetyService.updateHazardType(h.id, data);
                    } else {
                        res = await SafetyService.createHazardType(data);
                    }
                    if (res.code === 200 || res.code === 201) {
                        Toast.show(isEdit ? '更新成功' : '创建成功', 'success');
                        this.loadTypesTab();
                        this.loadHazardTypes();
                        return true;
                    } else {
                        Toast.error(res.message);
                        return false;
                    }
                } catch (e) { Toast.error('操作失败'); return false; }
            }
        });
    },

    async editHazardType(id) {
        const ht = this.hazardTypes.find(t => t.id === id);
        if (ht) this.showHazardTypeForm(ht);
    },

    async deleteHazardType(id) {
        const confirmed = await Modal.confirm('确定要删除该隐患类型吗？');
        if (!confirmed) return;
        try {
            const res = await SafetyService.deleteHazardType(id);
            if (res.code === 200) {
                Toast.show('删除成功', 'success');
                this.loadTypesTab();
                this.loadHazardTypes();
            } else { Toast.error(res.message); }
        } catch (e) { Toast.error('删除失败'); }
    },

    async loadTasksTab() {
        this.renderTasksTab();
    },

    renderTasksTab() {
        const content = document.getElementById('safetyTabContent');
        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:flex-end;">
                <button class="btn btn-primary" id="addInspectionTaskBtn">+ 新增排查任务</button>
            </div>
            <div id="inspectionTasksTable">加载中...</div>
        `;
        document.getElementById('addInspectionTaskBtn')?.addEventListener('click', () => this.showInspectionTaskForm());
        this.loadInspectionTasks();
    },

    async loadInspectionTasks() {
        try {
            const res = await SafetyService.getInspectionTasks({ size: 100 });
            if (res.code === 200) {
                const tasks = res.data.items || [];
                const typeMap = { plan: '计划性', periodic: '周期性', temporary: '临时' };
                const periodMap = { daily: '每日', weekly: '每周', monthly: '每月', quarterly: '每季度' };
                const wrap = document.getElementById('inspectionTasksTable');
                if (wrap) {
                    wrap.innerHTML = tasks.length === 0 ? '<div style="text-align:center;padding:40px;color:var(--text-secondary);">暂无排查任务</div>' : `
                    <table class="data-table">
                        <thead><tr><th>编号</th><th>名称</th><th>类型</th><th>周期</th><th>负责人</th><th>覆盖区域</th><th>下次执行</th><th>操作</th></tr></thead>
                        <tbody>
                            ${tasks.map(t => `
                                <tr>
                                    <td>${t.task_code}</td>
                                    <td>${t.task_name}</td>
                                    <td>${typeMap[t.task_type] || t.task_type}</td>
                                    <td>${periodMap[t.period] || t.period || '-'}</td>
                                    <td>${t.responsible_person || '-'}</td>
                                    <td>${t.area || '-'}</td>
                                    <td>${t.next_execution || '-'}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline" onclick="SafetyPage.editInspectionTask(${t.id})">编辑</button>
                                        <button class="btn btn-sm btn-danger" onclick="SafetyPage.deleteInspectionTask(${t.id})">删除</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>`;
                }
            }
        } catch (e) { Toast.error('加载排查任务失败'); }
    },

    showInspectionTaskForm(existingTask) {
        const isEdit = !!existingTask;
        const t = existingTask || {};
        this.openModal({
            title: isEdit ? '编辑排查任务' : '新增排查任务',
            width: '600px',
            content: `
                <form id="itForm">
                    <div class="form-group">
                        <label>任务编号 *</label>
                        <input type="text" class="form-control" name="task_code" value="${t.task_code || ''}" ${isEdit ? 'readonly' : ''}>
                    </div>
                    <div class="form-group">
                        <label>任务名称 *</label>
                        <input type="text" class="form-control" name="task_name" value="${t.task_name || ''}">
                    </div>
                    <div class="form-group">
                        <label>任务类型</label>
                        <select class="form-control" name="task_type">
                            <option value="plan" ${t.task_type === 'plan' || !t.task_type ? 'selected' : ''}>计划性</option>
                            <option value="periodic" ${t.task_type === 'periodic' ? 'selected' : ''}>周期性</option>
                            <option value="temporary" ${t.task_type === 'temporary' ? 'selected' : ''}>临时</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>周期</label>
                        <select class="form-control" name="period">
                            <option value="">请选择</option>
                            <option value="daily" ${t.period === 'daily' ? 'selected' : ''}>每日</option>
                            <option value="weekly" ${t.period === 'weekly' ? 'selected' : ''}>每周</option>
                            <option value="monthly" ${t.period === 'monthly' ? 'selected' : ''}>每月</option>
                            <option value="quarterly" ${t.period === 'quarterly' ? 'selected' : ''}>每季度</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>负责人</label>
                        <input type="text" class="form-control" name="responsible_person" value="${t.responsible_person || ''}">
                    </div>
                    <div class="form-group">
                        <label>覆盖区域</label>
                        <input type="text" class="form-control" name="area" value="${t.area || ''}">
                    </div>
                    <div class="form-group">
                        <label>下次执行时间</label>
                        <input type="datetime-local" class="form-control" name="next_execution" value="${t.next_execution ? t.next_execution.replace(' ', 'T').substring(0, 16) : ''}">
                    </div>
                    <div class="form-group">
                        <label>描述</label>
                        <textarea class="form-control" name="description" rows="2">${t.description || ''}</textarea>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('itForm');
                const data = {
                    task_code: form.task_code.value,
                    task_name: form.task_name.value,
                    task_type: form.task_type.value,
                    period: form.period.value,
                    responsible_person: form.responsible_person.value,
                    area: form.area.value,
                    description: form.description.value
                };
                if (form.next_execution.value) {
                    data.next_execution = form.next_execution.value.replace('T', ' ') + ':00';
                }
                if (!data.task_code || !data.task_name) {
                    Toast.error('请填写编号和名称');
                    return false;
                }
                try {
                    let res;
                    if (isEdit) {
                        res = await SafetyService.updateInspectionTask(t.id, data);
                    } else {
                        res = await SafetyService.createInspectionTask(data);
                    }
                    if (res.code === 200 || res.code === 201) {
                        Toast.show(isEdit ? '更新成功' : '创建成功', 'success');
                        this.loadTasksTab();
                        return true;
                    } else {
                        Toast.error(res.message);
                        return false;
                    }
                } catch (e) { Toast.error('操作失败'); return false; }
            }
        });
    },

    async editInspectionTask(id) {
        try {
            const res = await SafetyService.getInspectionTasks({ size: 100 });
            if (res.code === 200) {
                const task = (res.data.items || []).find(t => t.id === id);
                if (task) this.showInspectionTaskForm(task);
            }
        } catch (e) { Toast.error('获取数据失败'); }
    },

    async deleteInspectionTask(id) {
        const confirmed = await Modal.confirm('确定要删除该排查任务吗？');
        if (!confirmed) return;
        try {
            const res = await SafetyService.deleteInspectionTask(id);
            if (res.code === 200) {
                Toast.show('删除成功', 'success');
                this.loadTasksTab();
            } else { Toast.error(res.message); }
        } catch (e) { Toast.error('删除失败'); }
    }
};

window.SafetyPage = SafetyPage;
