/**
 * 巡视分组管理页面
 */
const PatrolGroupPage = {
    groups: [],
    allCameras: [],
    editingGroup: null,
    editingGroupCameras: [],

    init() {
        this.render();
        this.loadGroups();
    },

    async loadGroups() {
        try {
            const response = await VideoMonitorService.getGroups({ size: 100 });
            if (response.code === 200) {
                this.groups = response.data.items || [];
                this.renderList();
            }
        } catch (e) {
            Toast.error('加载分组列表失败');
        }
    },

    async loadAllCameras() {
        try {
            const response = await VideoMonitorService.getAllCameras();
            if (response.code === 200) {
                this.allCameras = response.data || [];
            }
        } catch (e) {
            console.error('加载摄像头失败:', e);
        }
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">巡视分组管理</h3>
                </div>
                <div class="card-body">
                    <div class="toolbar">
                        <div class="toolbar-left">
                            <span style="color: var(--text-secondary);">提示：编辑分组时可拖拽摄像头到分组中</span>
                        </div>
                        <div class="toolbar-right">
                            <button class="btn btn-success" id="addGroupBtn">+ 新增分组</button>
                        </div>
                    </div>
                    <div id="groupList"></div>
                </div>
            </div>
        `;
        document.getElementById('addGroupBtn')?.addEventListener('click', () => this.openModal());
    },

    renderList() {
        const listContainer = document.getElementById('groupList');
        if (!this.groups.length) {
            listContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">👥</div>
                    <div>暂无分组数据</div>
                </div>
            `;
            return;
        }

        const layoutMap = { '1': '单画面', '4': '4宫格', '9': '9宫格' };

        const cards = this.groups.map(g => `
            <div class="equipment-card" style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 16px; font-weight: 600; margin-bottom: 4px;">
                            ${g.group_name || '-'}
                        </div>
                        <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">
                            布局：<span class="badge badge-info">${layoutMap[g.layout] || g.layout}</span>
                            &nbsp;&nbsp;摄像头数量：<strong>${g.camera_count || 0}</strong>
                            &nbsp;&nbsp;${g.description ? ' | ' + g.description : ''}
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-primary" onclick="PatrolGroupPage.openWall(${g.id})">📺 打开视频墙</button>
                        <button class="btn btn-sm btn-primary" onclick="PatrolGroupPage.edit(${g.id})">编辑</button>
                        <button class="btn btn-sm btn-danger" onclick="PatrolGroupPage.delete(${g.id})">删除</button>
                    </div>
                </div>
            </div>
        `).join('');

        listContainer.innerHTML = cards;
    },

    async openModal(groupId = null) {
        await this.loadAllCameras();
        this.editingGroupCameras = [];
        let group = { group_name: '', layout: '4', description: '' };

        if (groupId) {
            try {
                const response = await VideoMonitorService.getGroup(groupId);
                if (response.code === 200) {
                    group = response.data;
                    this.editingGroupCameras = (group.cameras || []).map(c => ({ id: c.id, camera_code: c.camera_code, camera_name: c.camera_name, online_status: c.online_status }));
                }
            } catch (e) {
                Toast.error('加载分组详情失败');
                return;
            }
        }

        const html = `
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h3>${groupId ? '编辑分组' : '新增分组'}</h3>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>分组名称 *</label>
                        <input type="text" class="form-control" id="pgName" value="${group.group_name || ''}">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div class="form-group">
                            <label>推荐布局</label>
                            <select class="form-control" id="pgLayout">
                                <option value="1" ${group.layout === '1' ? 'selected' : ''}>单画面</option>
                                <option value="4" ${group.layout === '4' ? 'selected' : ''}>4宫格</option>
                                <option value="9" ${group.layout === '9' ? 'selected' : ''}>9宫格</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>&nbsp;</label>
                            <span style="font-size: 12px; color: var(--text-secondary); display: block; padding: 6px 0;">
                                共选 <strong id="pgSelectedCount">0</strong> 个摄像头
                            </span>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>描述</label>
                        <textarea class="form-control" id="pgDesc" rows="2">${group.description || ''}</textarea>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                        <div>
                            <label style="font-weight: 600; margin-bottom: 8px; display: block;">
                                可选摄像头 <span style="font-weight: normal; color: var(--text-secondary); font-size: 12px;">(拖拽到右侧)</span>
                            </label>
                            <div id="pgAvailableList" style="min-height: 240px; max-height: 280px; overflow-y: auto; border: 2px dashed var(--border-color); border-radius: 8px; padding: 8px;">
                                ${this.renderCameraList('available')}
                            </div>
                        </div>
                        <div>
                            <label style="font-weight: 600; margin-bottom: 8px; display: block;">
                                已选摄像头 <span style="font-weight: normal; color: var(--text-secondary); font-size: 12px;">(拖拽排序/拖出移除)</span>
                            </label>
                            <div id="pgSelectedList" style="min-height: 240px; max-height: 280px; overflow-y: auto; border: 2px dashed var(--primary-color); border-radius: 8px; padding: 8px; background: rgba(0,123,255,0.02);">
                                ${this.renderCameraList('selected')}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline" id="pgCancelBtn">取消</button>
                    <button class="btn btn-primary" id="pgSaveBtn">保存</button>
                </div>
            </div>
        `;

        Modal.showHtml(html);
        document.getElementById('pgCancelBtn')?.addEventListener('click', () => Modal.close());
        document.getElementById('pgSaveBtn')?.addEventListener('click', () => this.saveGroup(groupId));
        this.bindDragEvents();
        this.updateSelectedCount();
    },

    renderCameraList(type) {
        let cameras;
        if (type === 'available') {
            const selectedIds = this.editingGroupCameras.map(c => c.id);
            cameras = this.allCameras.filter(c => !selectedIds.includes(c.id));
        } else {
            cameras = this.editingGroupCameras;
        }

        if (!cameras.length) {
            return `<div style="text-align: center; padding: 24px; color: var(--text-muted); font-size: 13px;">
                ${type === 'available' ? '全部已选择' : '请从左侧拖拽摄像头'}
            </div>`;
        }

        return cameras.map((c, idx) => `
            <div class="pg-cam-item"
                 draggable="true"
                 data-camera-id="${c.id}"
                 data-camera-code="${c.camera_code || ''}"
                 data-camera-name="${c.camera_name || ''}"
                 data-camera-status="${c.online_status || 'offline'}"
                 data-source="${type}"
                 data-idx="${idx}"
                 style="display: flex; align-items: center; gap: 8px; padding: 8px 10px; margin-bottom: 6px; background: white; border: 1px solid var(--border-color); border-radius: 6px; cursor: grab; transition: all 0.2s;">
                <span style="font-size: 18px;">📷</span>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 13px; font-weight: 500;">${c.camera_name || '未命名'}</div>
                    <div style="font-size: 11px; color: var(--text-secondary);">${c.camera_code || ''}</div>
                </div>
                <span class="badge ${c.online_status === 'online' ? 'badge-success' : 'badge-secondary'}" style="font-size: 10px;">
                    ${c.online_status === 'online' ? '在线' : '离线'}
                </span>
            </div>
        `).join('');
    },

    bindDragEvents() {
        const items = document.querySelectorAll('.pg-cam-item');
        items.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('cameraId', item.dataset.cameraId);
                e.dataTransfer.setData('cameraCode', item.dataset.cameraCode);
                e.dataTransfer.setData('cameraName', item.dataset.cameraName);
                e.dataTransfer.setData('cameraStatus', item.dataset.cameraStatus);
                e.dataTransfer.setData('source', item.dataset.source);
                e.dataTransfer.setData('idx', item.dataset.idx);
                item.style.opacity = '0.5';
            });
            item.addEventListener('dragend', () => {
                item.style.opacity = '1';
            });
        });

        const selectedList = document.getElementById('pgSelectedList');
        if (selectedList) {
            selectedList.addEventListener('dragover', (e) => { e.preventDefault(); });
            selectedList.addEventListener('drop', (e) => {
                e.preventDefault();
                const source = e.dataTransfer.getData('source');
                const cameraId = parseInt(e.dataTransfer.getData('cameraId'));
                const cameraCode = e.dataTransfer.getData('cameraCode');
                const cameraName = e.dataTransfer.getData('cameraName');
                const cameraStatus = e.dataTransfer.getData('cameraStatus');

                if (source === 'available') {
                    if (!this.editingGroupCameras.find(c => c.id === cameraId)) {
                        this.editingGroupCameras.push({ id: cameraId, camera_code: cameraCode, camera_name: cameraName, online_status: cameraStatus });
                    }
                }
                this.refreshDragLists();
            });
        }

        const availableList = document.getElementById('pgAvailableList');
        if (availableList) {
            availableList.addEventListener('dragover', (e) => { e.preventDefault(); });
            availableList.addEventListener('drop', (e) => {
                e.preventDefault();
                const source = e.dataTransfer.getData('source');
                const cameraId = parseInt(e.dataTransfer.getData('cameraId'));
                if (source === 'selected') {
                    this.editingGroupCameras = this.editingGroupCameras.filter(c => c.id !== cameraId);
                }
                this.refreshDragLists();
            });
        }
    },

    refreshDragLists() {
        const availableList = document.getElementById('pgAvailableList');
        const selectedList = document.getElementById('pgSelectedList');
        if (availableList) availableList.innerHTML = this.renderCameraList('available');
        if (selectedList) selectedList.innerHTML = this.renderCameraList('selected');
        this.bindDragEvents();
        this.updateSelectedCount();
    },

    updateSelectedCount() {
        const el = document.getElementById('pgSelectedCount');
        if (el) el.textContent = this.editingGroupCameras.length;
    },

    async saveGroup(groupId) {
        const data = {
            group_name: document.getElementById('pgName').value.trim(),
            layout: document.getElementById('pgLayout').value,
            description: document.getElementById('pgDesc').value.trim(),
            camera_ids: this.editingGroupCameras.map(c => c.id)
        };

        if (!data.group_name) {
            Toast.warning('请填写分组名称');
            return;
        }

        try {
            let response;
            if (groupId) {
                response = await VideoMonitorService.updateGroup(groupId, data);
            } else {
                response = await VideoMonitorService.createGroup(data);
            }
            if (response.code === 200) {
                Toast.success(groupId ? '更新成功' : '创建成功');
                Modal.close();
                this.loadGroups();
            } else {
                Toast.error(response.message || '保存失败');
            }
        } catch (e) {
            Toast.error('保存失败');
        }
    },

    async edit(groupId) {
        this.openModal(groupId);
    },

    async delete(groupId) {
        const confirmed = await Modal.confirm('确定要删除该分组吗？');
        if (!confirmed) return;
        try {
            const response = await VideoMonitorService.deleteGroup(groupId);
            if (response.code === 200) {
                Toast.success('删除成功');
                this.loadGroups();
            } else {
                Toast.error(response.message || '删除失败');
            }
        } catch (e) {
            Toast.error('删除失败');
        }
    },

    openWall(groupId) {
        if (window.VideoWallPage) {
            VideoWallPage.targetGroupId = groupId;
            App.navigate('video-wall');
        } else {
            Toast.warning('视频墙页面未加载');
        }
    }
};

window.PatrolGroupPage = PatrolGroupPage;
