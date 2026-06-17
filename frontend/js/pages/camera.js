/**
 * 摄像头档案管理页面
 */
const CameraPage = {
    cameras: [],
    productionLines: [],
    equipments: [],
    editingCamera: null,

    init() {
        this.render();
        this.loadProductionLines();
        this.loadEquipments();
        this.loadCameras();
    },

    async loadProductionLines() {
        try {
            const response = await Request.get('/production/lines');
            if (response.code === 200) {
                this.productionLines = response.data.items || response.data || [];
            }
        } catch (e) {
            console.error('加载生产线失败:', e);
        }
    },

    async loadEquipments() {
        try {
            const response = await Request.get('/production/equipments');
            if (response.code === 200) {
                this.equipments = response.data.items || response.data || [];
            }
        } catch (e) {
            console.error('加载设备失败:', e);
        }
    },

    async loadCameras(page = 1) {
        try {
            const keyword = document.getElementById('cameraSearch')?.value || '';
            const onlineStatus = document.getElementById('cameraStatusFilter')?.value || '';
            const response = await VideoMonitorService.getCameras({
                page, size: 10,
                keyword: keyword || undefined,
                online_status: onlineStatus || undefined
            });
            if (response.code === 200) {
                this.cameras = response.data.items || [];
                this.renderTable();
            }
        } catch (e) {
            Toast.error('加载摄像头列表失败');
        }
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">摄像头档案管理</h3>
                </div>
                <div class="card-body">
                    <div class="toolbar">
                        <div class="toolbar-left">
                            <input type="text" class="form-control" id="cameraSearch" placeholder="搜索编号/名称/IP..." style="width: 200px;">
                            <select class="form-control" id="cameraStatusFilter" style="width: 120px; margin-left: 8px;">
                                <option value="">全部状态</option>
                                <option value="online">在线</option>
                                <option value="offline">离线</option>
                            </select>
                            <button class="btn btn-primary" id="cameraSearchBtn" style="margin-left: 8px;">🔍 搜索</button>
                        </div>
                        <div class="toolbar-right">
                            <button class="btn btn-success" id="addCameraBtn">+ 新增摄像头</button>
                        </div>
                    </div>
                    <div id="cameraTable"></div>
                </div>
            </div>
        `;

        document.getElementById('addCameraBtn')?.addEventListener('click', () => this.openModal());
        document.getElementById('cameraSearchBtn')?.addEventListener('click', () => this.loadCameras());
        document.getElementById('cameraSearch')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.loadCameras();
        });
        document.getElementById('cameraStatusFilter')?.addEventListener('change', () => this.loadCameras());
    },

    renderTable() {
        const tableContainer = document.getElementById('cameraTable');
        if (!this.cameras.length) {
            tableContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">📷</div>
                    <div>暂无摄像头数据</div>
                </div>
            `;
            return;
        }

        const rows = this.cameras.map(cam => `
            <tr>
                <td>${cam.camera_code || '-'}</td>
                <td>${cam.camera_name || '-'}</td>
                <td>${cam.ip_address || '-'}</td>
                <td>${cam.area || cam.line_name || '-'}</td>
                <td>
                    <span class="badge ${cam.online_status === 'online' ? 'badge-success' : 'badge-secondary'}">
                        ${cam.online_status === 'online' ? '● 在线' : '○ 离线'}
                    </span>
                </td>
                <td>${cam.last_heartbeat ? this.formatTime(cam.last_heartbeat) : '-'}</td>
                <td>${cam.equipment_count || 0}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="CameraPage.capture(${cam.id})">抓图</button>
                    <button class="btn btn-sm btn-primary" onclick="CameraPage.edit(${cam.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="CameraPage.delete(${cam.id})">删除</button>
                </td>
            </tr>
        `).join('');

        tableContainer.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>编号</th>
                        <th>名称</th>
                        <th>IP地址</th>
                        <th>所属区域/生产线</th>
                        <th>状态</th>
                        <th>最后心跳</th>
                        <th>关联设备</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    },

    formatTime(str) {
        if (!str) return '-';
        try {
            const d = new Date(str);
            return d.toLocaleString('zh-CN', {
                month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
        } catch { return str; }
    },

    async openModal(cameraId = null) {
        this.editingCamera = null;
        let camera = { camera_code: '', camera_name: '', ip_address: '', stream_url: '', line_id: '', area: '', online_status: 'offline', description: '', equipment_ids: [] };

        if (cameraId) {
            try {
                const response = await VideoMonitorService.getCamera(cameraId);
                if (response.code === 200) {
                    camera = response.data;
                    this.editingCamera = camera;
                    camera.equipment_ids = (camera.equipments || []).map(e => e.equipment_id);
                }
            } catch (e) {
                Toast.error('加载摄像头详情失败');
                return;
            }
        }

        const lineOptions = this.productionLines.map(l =>
            `<option value="${l.id}" ${camera.line_id === l.id ? 'selected' : ''}>${l.line_name}</option>`
        ).join('');

        const equipmentOptions = this.equipments.map(e => {
            const checked = (camera.equipment_ids || []).includes(e.id) ? 'checked' : '';
            return `
                <label style="display: flex; align-items: center; gap: 6px; padding: 4px 0;">
                    <input type="checkbox" class="eq-checkbox" value="${e.id}" ${checked}>
                    <span>${e.equipment_code} - ${e.equipment_name}</span>
                </label>
            `;
        }).join('');

        const html = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3>${cameraId ? '编辑摄像头' : '新增摄像头'}</h3>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>摄像头编号 *</label>
                        <input type="text" class="form-control" id="camCode" value="${camera.camera_code || ''}" placeholder="例如：CAM-001">
                    </div>
                    <div class="form-group">
                        <label>摄像头名称 *</label>
                        <input type="text" class="form-control" id="camName" value="${camera.camera_name || ''}" placeholder="例如：车间入口摄像头">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div class="form-group">
                            <label>IP地址</label>
                            <input type="text" class="form-control" id="camIp" value="${camera.ip_address || ''}" placeholder="例如：192.168.1.100">
                        </div>
                        <div class="form-group">
                            <label>在线状态</label>
                            <select class="form-control" id="camStatus">
                                <option value="online" ${camera.online_status === 'online' ? 'selected' : ''}>在线</option>
                                <option value="offline" ${camera.online_status === 'offline' ? 'selected' : ''}>离线</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>流地址 (RTSP/HTTP)</label>
                        <input type="text" class="form-control" id="camStream" value="${camera.stream_url || ''}" placeholder="例如：rtsp://192.168.1.100/stream">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div class="form-group">
                            <label>所属生产线</label>
                            <select class="form-control" id="camLine">
                                <option value="">-- 请选择 --</option>
                                ${lineOptions}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>所属区域</label>
                            <input type="text" class="form-control" id="camArea" value="${camera.area || ''}" placeholder="例如：一号车间">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>关联设备（可多选）</label>
                        <div style="max-height: 120px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 4px; padding: 8px;">
                            ${equipmentOptions || '<span style="color: var(--text-muted);">暂无设备</span>'}
                        </div>
                    </div>
                    <div class="form-group">
                        <label>描述</label>
                        <textarea class="form-control" id="camDesc" rows="2">${camera.description || ''}</textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline" id="camCancelBtn">取消</button>
                    <button class="btn btn-primary" id="camSaveBtn">保存</button>
                </div>
            </div>
        `;

        Modal.showHtml(html);
        document.getElementById('camCancelBtn')?.addEventListener('click', () => Modal.close());
        document.getElementById('camSaveBtn')?.addEventListener('click', () => this.saveCamera(cameraId));
    },

    async saveCamera(cameraId) {
        const equipmentIds = Array.from(document.querySelectorAll('.eq-checkbox:checked')).map(cb => parseInt(cb.value));
        const data = {
            camera_code: document.getElementById('camCode').value.trim(),
            camera_name: document.getElementById('camName').value.trim(),
            ip_address: document.getElementById('camIp').value.trim(),
            stream_url: document.getElementById('camStream').value.trim(),
            line_id: document.getElementById('camLine').value ? parseInt(document.getElementById('camLine').value) : null,
            area: document.getElementById('camArea').value.trim(),
            online_status: document.getElementById('camStatus').value,
            description: document.getElementById('camDesc').value.trim(),
            equipment_ids: equipmentIds
        };

        if (!data.camera_code || !data.camera_name) {
            Toast.warning('请填写编号和名称');
            return;
        }

        try {
            let response;
            if (cameraId) {
                response = await VideoMonitorService.updateCamera(cameraId, data);
            } else {
                response = await VideoMonitorService.createCamera(data);
            }
            if (response.code === 200) {
                Toast.success(cameraId ? '更新成功' : '创建成功');
                Modal.close();
                this.loadCameras();
            } else {
                Toast.error(response.message || '保存失败');
            }
        } catch (e) {
            Toast.error('保存失败');
        }
    },

    async edit(cameraId) {
        this.openModal(cameraId);
    },

    async delete(cameraId) {
        const confirmed = await Modal.confirm('确定要删除该摄像头吗？');
        if (!confirmed) return;
        try {
            const response = await VideoMonitorService.deleteCamera(cameraId);
            if (response.code === 200) {
                Toast.success('删除成功');
                this.loadCameras();
            } else {
                Toast.error(response.message || '删除失败');
            }
        } catch (e) {
            Toast.error('删除失败');
        }
    },

    async capture(cameraId) {
        try {
            const response = await VideoMonitorService.manualCapture(cameraId);
            if (response.code === 200) {
                Toast.success('抓图成功');
                this.showCaptureImage(response.data.image_base64);
            } else {
                Toast.error(response.message || '抓图失败');
            }
        } catch (e) {
            Toast.error('抓图失败');
        }
    },

    showCaptureImage(imageBase64) {
        const html = `
            <div class="modal-content" style="max-width: 720px;">
                <div class="modal-header">
                    <h3>抓图预览</h3>
                </div>
                <div class="modal-body" style="text-align: center;">
                    <img src="${imageBase64}" style="max-width: 100%; border-radius: 8px;">
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="Modal.close()">关闭</button>
                </div>
            </div>
        `;
        Modal.showHtml(html);
    }
};

window.CameraPage = CameraPage;
