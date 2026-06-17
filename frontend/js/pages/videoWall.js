/**
 * 视频墙页面
 */
const VideoWallPage = {
    targetGroupId: null,
    groups: [],
    currentGroup: null,
    currentLayout: '4',
    cameras: [],
    refreshTimer: null,

    PLACEHOLDER_IMG: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NDAiIGhlaWdodD0iMzYwIiB2aWV3Qm94PSIwIDAgNjQwIDM2MCI+" +
        "<rect width=\"640\" height=\"360\" fill=\"#1a1a2e\"/>" +
        "<circle cx=\"50%\" cy=\"40%\" r=\"50\" fill=\"#333\" stroke=\"#555\" stroke-width=\"3\"/>" +
        "<rect x=\"35%\" y=\"55%\" width=\"30%\" height=\"8\" rx=\"4\" fill=\"#333\"/>" +
        "<rect x=\"25%\" y=\"70%\" width=\"50%\" height=\"6\" rx=\"3\" fill=\"#2a2a3e\"/>" +
        "<text x=\"50%\" y=\"90%\" font-family=\"Arial\" font-size=\"20\" fill=\"#666\" text-anchor=\"middle\">暂无视频信号</text>" +
        "</svg>",

    init() {
        this.render();
        this.loadGroups();
        this.startHeartbeatRefresh();
    },

    destroy() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    },

    startHeartbeatRefresh() {
        this.refreshTimer = setInterval(() => {
            if (this.currentGroup) {
                this.loadGroupCameras(this.currentGroup.id, true);
            }
        }, 10000);
    },

    async loadGroups() {
        try {
            const response = await VideoMonitorService.getAllGroups();
            if (response.code === 200) {
                this.groups = response.data || [];
                this.renderGroupSelect();

                if (this.targetGroupId) {
                    this.selectGroup(this.targetGroupId);
                    this.targetGroupId = null;
                } else if (this.groups.length > 0) {
                    this.selectGroup(this.groups[0].id);
                }
            }
        } catch (e) {
            Toast.error('加载分组列表失败');
        }
    },

    renderGroupSelect() {
        const select = document.getElementById('vwGroupSelect');
        if (!select) return;
        select.innerHTML = this.groups.map(g =>
            `<option value="${g.id}">${g.group_name} (${g.camera_count || 0}路)</option>`
        ).join('');
    },

    async selectGroup(groupId) {
        const select = document.getElementById('vwGroupSelect');
        if (select) select.value = groupId;
        await this.loadGroupCameras(groupId);
    },

    async loadGroupCameras(groupId, silent = false) {
        try {
            const response = await VideoMonitorService.getGroupOnlineCameras(groupId);
            if (response.code === 200) {
                this.currentGroup = {
                    id: response.data.group_id,
                    group_name: response.data.group_name,
                    layout: response.data.layout
                };
                this.currentLayout = response.data.layout;
                this.cameras = response.data.cameras || [];

                if (!silent) {
                    this.renderLayoutSelector();
                }
                this.renderVideoGrid();
                this.renderStats(response.data.online_count, response.data.total_count);
            }
        } catch (e) {
            if (!silent) Toast.error('加载分组摄像头失败');
        }
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div style="height: calc(100vh - var(--header-height, 60px) - 48px); display: flex; flex-direction: column;">
                <div class="card" style="margin-bottom: 12px;">
                    <div class="card-body" style="padding: 12px 20px;">
                        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-weight: 600;">📺 视频墙</span>
                            </div>
                            <div>
                                <label style="margin-right: 6px; color: var(--text-secondary); font-size: 13px;">巡视分组：</label>
                                <select class="form-control" id="vwGroupSelect" style="width: 200px; display: inline-block;"></select>
                            </div>
                            <div>
                                <label style="margin-right: 6px; color: var(--text-secondary); font-size: 13px;">布局：</label>
                                <div id="vwLayoutSelector" style="display: inline-flex; gap: 4px;"></div>
                            </div>
                            <div style="flex: 1;"></div>
                            <div id="vwStats" style="font-size: 13px; color: var(--text-secondary);"></div>
                            <button class="btn btn-sm btn-primary" id="vwRefreshBtn">🔄 刷新</button>
                        </div>
                    </div>
                </div>
                <div class="card" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
                    <div class="card-body" id="vwVideoContainer" style="flex: 1; overflow: auto; padding: 16px;">
                        <div style="text-align: center; padding: 80px; color: var(--text-secondary);">
                            <div style="font-size: 48px; margin-bottom: 16px;">📺</div>
                            <div>请选择巡视分组</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('vwGroupSelect')?.addEventListener('change', (e) => {
            this.selectGroup(parseInt(e.target.value));
        });
        document.getElementById('vwRefreshBtn')?.addEventListener('click', () => {
            if (this.currentGroup) this.loadGroupCameras(this.currentGroup.id);
        });
    },

    renderLayoutSelector() {
        const container = document.getElementById('vwLayoutSelector');
        if (!container) return;
        const layouts = [
            { key: '1', label: '1×1' },
            { key: '4', label: '2×2' },
            { key: '9', label: '3×3' }
        ];
        container.innerHTML = layouts.map(l => `
            <button class="btn btn-sm ${this.currentLayout === l.key ? 'btn-primary' : 'btn-outline'}"
                    onclick="VideoWallPage.changeLayout('${l.key}')">${l.label}</button>
        `).join('');
    },

    changeLayout(layout) {
        this.currentLayout = layout;
        this.renderLayoutSelector();
        this.renderVideoGrid();
    },

    renderStats(online, total) {
        const el = document.getElementById('vwStats');
        if (el) {
            el.innerHTML = `
                <span class="badge badge-success">● 在线 ${online}</span>
                <span class="badge badge-secondary" style="margin-left: 4px;">共 ${total} 路</span>
            `;
        }
    },

    renderVideoGrid() {
        const container = document.getElementById('vwVideoContainer');
        if (!container) return;

        const layoutNum = parseInt(this.currentLayout);
        const cols = layoutNum === 1 ? 1 : layoutNum === 4 ? 2 : 3;

        if (!this.cameras || this.cameras.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 80px; color: var(--text-secondary);">
                    <div style="font-size: 48px; margin-bottom: 16px;">📷</div>
                    <div>当前分组暂无在线摄像头</div>
                </div>
            `;
            return;
        }

        const slots = Math.max(layoutNum, this.cameras.length);
        let cells = '';
        for (let i = 0; i < slots; i++) {
            const cam = this.cameras[i];
            cells += this.renderCell(cam, i);
        }

        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(${cols}, 1fr); gap: 12px; height: 100%; min-height: 400px;">
                ${cells}
            </div>
        `;
    },

    renderCell(cam, index) {
        if (!cam) {
            return `
                <div style="border: 2px dashed var(--border-color); border-radius: 8px; display: flex; align-items: center; justify-content: center; background: var(--bg-light); color: var(--text-muted); min-height: 180px;">
                    空位 ${index + 1}
                </div>
            `;
        }

        const isOnline = cam.online_status === 'online';

        return `
            <div style="border-radius: 8px; overflow: hidden; background: #000; position: relative; min-height: 180px; display: flex; flex-direction: column;">
                <div style="position: absolute; top: 8px; left: 8px; z-index: 2; display: flex; align-items: center; gap: 6px;">
                    <span class="vw-heartbeat ${isOnline ? 'online' : 'offline'}"></span>
                    <span style="color: white; font-size: 12px; text-shadow: 0 1px 3px rgba(0,0,0,0.8); font-weight: 500;">
                        ${cam.camera_name || '摄像头' + (index + 1)}
                    </span>
                </div>
                <div style="position: absolute; top: 8px; right: 8px; z-index: 2;">
                    <span style="background: rgba(0,0,0,0.6); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">
                        ${isOnline ? '● 在线' : '○ 离线'}
                    </span>
                </div>
                <div style="flex: 1; display: flex; align-items: center; justify-content: center; background: #0a0a14;">
                    <img src="${this.PLACEHOLDER_IMG}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                </div>
                <div style="background: rgba(0,0,0,0.85); padding: 6px 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="color: #ccc; font-size: 11px;">
                        ${cam.camera_code || ''} ${cam.ip_address ? ' | ' + cam.ip_address : ''}
                    </div>
                    <button class="btn btn-sm btn-primary" style="font-size: 11px; padding: 2px 8px;"
                            onclick="VideoWallPage.capture(${cam.id})">📷 抓图</button>
                </div>
            </div>
        `;
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

window.VideoWallPage = VideoWallPage;
