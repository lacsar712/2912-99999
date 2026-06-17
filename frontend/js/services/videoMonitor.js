/**
 * 视频监控服务
 */
const VideoMonitorService = {
    async getCameras(params = {}) {
        return await Request.get('/video-monitor/cameras', params);
    },

    async getAllCameras() {
        return await Request.get('/video-monitor/cameras/all');
    },

    async getCamera(cameraId) {
        return await Request.get(`/video-monitor/cameras/${cameraId}`);
    },

    async createCamera(data) {
        return await Request.post('/video-monitor/cameras', data);
    },

    async updateCamera(cameraId, data) {
        return await Request.put(`/video-monitor/cameras/${cameraId}`, data);
    },

    async deleteCamera(cameraId) {
        return await Request.delete(`/video-monitor/cameras/${cameraId}`);
    },

    async reportHeartbeat(data) {
        return await Request.post('/video-monitor/cameras/heartbeat', data);
    },

    async getGroups(params = {}) {
        return await Request.get('/video-monitor/groups', params);
    },

    async getAllGroups() {
        return await Request.get('/video-monitor/groups/all');
    },

    async getGroup(groupId) {
        return await Request.get(`/video-monitor/groups/${groupId}`);
    },

    async getGroupOnlineCameras(groupId) {
        return await Request.get(`/video-monitor/groups/${groupId}/online-cameras`);
    },

    async createGroup(data) {
        return await Request.post('/video-monitor/groups', data);
    },

    async updateGroup(groupId, data) {
        return await Request.put(`/video-monitor/groups/${groupId}`, data);
    },

    async deleteGroup(groupId) {
        return await Request.delete(`/video-monitor/groups/${groupId}`);
    },

    async getCaptureRecords(params = {}) {
        return await Request.get('/video-monitor/captures', params);
    },

    async getCapturesByAlert(alertId) {
        return await Request.get(`/video-monitor/captures/alert/${alertId}`);
    },

    async getCaptureRecord(recordId) {
        return await Request.get(`/video-monitor/captures/${recordId}`);
    },

    async manualCapture(cameraId) {
        return await Request.post(`/video-monitor/captures/manual/${cameraId}`);
    },

    async triggerAlertCapture(data) {
        return await Request.post('/video-monitor/captures/alert-trigger', data);
    }
};

window.VideoMonitorService = VideoMonitorService;
